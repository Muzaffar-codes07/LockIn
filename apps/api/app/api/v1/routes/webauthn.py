"""WebAuthn passkey registration.

Two-step flow:
  1. POST ``/v1/webauthn/register/options`` — server generates challenge +
     options for ``navigator.credentials.create``.
  2. POST ``/v1/webauthn/register/verify`` — browser returns the attestation;
     server verifies and persists the credential.

The pending-challenge state lives in a process-local dict for this slice.
**TODO(week-3+):** replace with Redis-backed storage before any multi-instance
deploy. The dict is keyed by ``user_id`` with a 5-minute soft expiry checked
on read.
"""

from __future__ import annotations

import time
from base64 import urlsafe_b64encode
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Body, HTTPException, status
from sqlalchemy import select
from webauthn import generate_registration_options, verify_registration_response
from webauthn.helpers.cose import COSEAlgorithmIdentifier
from webauthn.helpers.structs import (
    AttestationConveyancePreference,
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.api.v1.deps import DbSession
from app.core.auth import CurrentUserDep
from app.core.config import settings
from app.db.models.credential import WebauthnCredential

router = APIRouter(prefix="/webauthn", tags=["webauthn"])

# Process-local challenge cache. See module docstring for the Redis follow-up.
_CHALLENGE_TTL_SECONDS = 300
_pending_challenges: dict[str, tuple[bytes, float]] = {}


def _put_challenge(user_id: str, challenge: bytes) -> None:
    _pending_challenges[user_id] = (challenge, time.monotonic())


def _pop_challenge(user_id: str) -> bytes | None:
    entry = _pending_challenges.pop(user_id, None)
    if entry is None:
        return None
    challenge, stamped_at = entry
    if time.monotonic() - stamped_at > _CHALLENGE_TTL_SECONDS:
        return None
    return challenge


def _b64url(value: bytes) -> str:
    return urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


@router.post("/register/options")
async def register_options(user: CurrentUserDep) -> dict[str, Any]:
    options = generate_registration_options(
        rp_id=settings.WEBAUTHN_RP_ID,
        rp_name="LockIn",
        user_id=user.user_id.encode("utf-8"),
        user_name=user.email or user.user_id,
        user_display_name=user.email or user.user_id,
        attestation=AttestationConveyancePreference.NONE,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
        supported_pub_key_algs=[
            COSEAlgorithmIdentifier.ECDSA_SHA_256,
            COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
        ],
    )
    _put_challenge(user.user_id, options.challenge)

    payload: dict[str, Any] = {
        "rp": {"id": options.rp.id, "name": options.rp.name},
        "user": {
            "id": _b64url(options.user.id),
            "name": options.user.name,
            "displayName": options.user.display_name,
        },
        "challenge": _b64url(options.challenge),
        "pubKeyCredParams": [
            {"type": "public-key", "alg": int(p.alg)} for p in options.pub_key_cred_params
        ],
        "timeout": options.timeout,
        "attestation": options.attestation.value,
    }

    sel = options.authenticator_selection
    if sel is not None:
        auth_sel: dict[str, str] = {}
        if sel.resident_key is not None:
            auth_sel["residentKey"] = sel.resident_key.value
        if sel.user_verification is not None:
            auth_sel["userVerification"] = sel.user_verification.value
        if auth_sel:
            payload["authenticatorSelection"] = auth_sel

    return payload


@router.post("/register/verify")
async def register_verify(
    db: DbSession,
    user: CurrentUserDep,
    body: Annotated[dict[str, Any], Body()],
) -> dict[str, str]:
    challenge = _pop_challenge(user.user_id)
    if challenge is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "no pending registration challenge for this user",
        )

    credential = body.get("credential")
    if not isinstance(credential, dict):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "missing 'credential' in body")

    try:
        verification = verify_registration_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=settings.WEBAUTHN_RP_ID,
            expected_origin=settings.WEBAUTHN_EXPECTED_ORIGIN,
        )
    except Exception as exc:  # webauthn raises subclassed errors; surface as 400
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"attestation failed: {exc}") from exc

    # Idempotency: if this credential already exists for this user, treat as success.
    existing = await db.scalar(
        select(WebauthnCredential).where(
            WebauthnCredential.credential_id == verification.credential_id
        )
    )
    if existing is not None:
        return {
            "status": "already_registered",
            "credential_id": _b64url(verification.credential_id),
        }

    record = WebauthnCredential(
        user_id=UUID(user.user_id),
        credential_id=verification.credential_id,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        transports=",".join(body.get("transports", [])) or None,
    )
    db.add(record)
    await db.commit()
    return {"status": "registered", "credential_id": _b64url(verification.credential_id)}
