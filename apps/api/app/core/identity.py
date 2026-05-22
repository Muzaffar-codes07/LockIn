"""Map an external OAuth subject to a stable internal UUID.

Auth is JWT-strategy: there is no `users` table, and the identity we receive
is Google's `sub` claim — a numeric string, not a UUID. The event schema and
every per-user table key on `UUID`. `user_uuid` derives a deterministic v5
UUID from the subject so Postgres rows and the `task.created` event stream
agree on one identifier per user.
"""

from __future__ import annotations

from uuid import UUID, uuid5

# Fixed namespace for user-identity derivation. Generated once for LockIn.
# NEVER change this value — changing it re-keys every existing user.
_USER_NAMESPACE = UUID("9f2a7c4e-0b1d-4e6a-8c3f-1a2b3c4d5e6f")


def user_uuid(subject: str) -> UUID:
    """Return the stable internal UUID for an OAuth subject (e.g. Google `sub`)."""
    return uuid5(_USER_NAMESPACE, subject)
