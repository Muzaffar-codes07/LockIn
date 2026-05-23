"""AES-GCM envelope encryption with versioned keys (spec §5)."""

from __future__ import annotations

import os

import pytest

from app.crypto.aes_gcm import EnvelopeCipher, KeyVersion


@pytest.fixture
def cipher(monkeypatch: pytest.MonkeyPatch) -> EnvelopeCipher:
    # 32-byte keys; v1 + v2 simulating a rotation in progress.
    monkeypatch.setenv("OAUTH_TOKEN_ENCRYPTION_KEY_V1", os.urandom(32).hex())
    monkeypatch.setenv("OAUTH_TOKEN_ENCRYPTION_KEY_V2", os.urandom(32).hex())
    return EnvelopeCipher.from_env(prefix="OAUTH_TOKEN_ENCRYPTION_KEY")


def test_encrypts_with_highest_version_and_round_trips(cipher: EnvelopeCipher) -> None:
    blob, version = cipher.encrypt(b"hello refresh token")
    assert version == KeyVersion(2)
    assert cipher.decrypt(blob, version) == b"hello refresh token"


def test_decrypts_legacy_version_after_rotation(cipher: EnvelopeCipher) -> None:
    blob_v1, _ = cipher.encrypt_with_version(b"old row", KeyVersion(1))
    assert cipher.decrypt(blob_v1, KeyVersion(1)) == b"old row"


def test_rejects_missing_version(cipher: EnvelopeCipher) -> None:
    with pytest.raises(KeyError):
        cipher.decrypt(b"garbage", KeyVersion(99))
