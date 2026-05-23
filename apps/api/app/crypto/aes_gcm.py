"""AES-GCM envelope encryption with versioned keys.

Used for at-rest encryption of OAuth refresh tokens (spec §5).
Rotation pattern documented in docs/runbooks/oauth-token-encryption-key-rotation.md.

Note: ``EnvelopeCipher.from_env`` iterates all env vars once at app startup.
It should be called during application initialisation, not inside request handlers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import NewType

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KeyVersion = NewType("KeyVersion", int)


@dataclass(frozen=True)
class EnvelopeCipher:
    """Holds N AES-GCM keys keyed by version; encrypts with the highest."""

    keys: dict[KeyVersion, bytes]

    @classmethod
    def from_env(cls, *, prefix: str) -> EnvelopeCipher:
        keys: dict[KeyVersion, bytes] = {}
        for name, value in os.environ.items():
            if not name.startswith(f"{prefix}_V"):
                continue
            try:
                version = KeyVersion(int(name.removeprefix(f"{prefix}_V")))
            except ValueError:
                continue
            raw = bytes.fromhex(value)
            if len(raw) != 32:
                raise ValueError(f"{name} must be 32 bytes hex (AES-256)")
            keys[version] = raw
        if not keys:
            raise RuntimeError(f"No {prefix}_V<n> env vars defined")
        return cls(keys=keys)

    @property
    def current_version(self) -> KeyVersion:
        return max(self.keys)

    def encrypt(self, plaintext: bytes) -> tuple[bytes, KeyVersion]:
        return self.encrypt_with_version(plaintext, self.current_version)

    def encrypt_with_version(
        self, plaintext: bytes, version: KeyVersion
    ) -> tuple[bytes, KeyVersion]:
        if version not in self.keys:
            raise KeyError(version)
        nonce = os.urandom(12)
        ciphertext = AESGCM(self.keys[version]).encrypt(nonce, plaintext, None)
        return nonce + ciphertext, version

    def decrypt(self, blob: bytes, version: KeyVersion) -> bytes:
        if version not in self.keys:
            raise KeyError(version)
        nonce, ciphertext = blob[:12], blob[12:]
        return AESGCM(self.keys[version]).decrypt(nonce, ciphertext, None)  # type: ignore[no-any-return]
