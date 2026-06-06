from __future__ import annotations

"""Small abstraction for storing/retrieving secrets locally.

Currently uses `keyring` (OS keychain). Falls back to an in-memory stub if
keyring backend isn't available.
"""

from dataclasses import dataclass
from typing import Optional

SERVICE = "jarvis"


@dataclass
class SecretStore:
    """Key/value secret store."""

    def set(self, key: str, value: str) -> None:
        raise NotImplementedError

    def get(self, key: str) -> Optional[str]:
        raise NotImplementedError


class KeyringSecretStore(SecretStore):
    def __init__(self, service: str = SERVICE):
        self.service = service
        import keyring

        self._keyring = keyring

    def set(self, key: str, value: str) -> None:
        # keyring handles encryption on supported platforms.
        self._keyring.set_password(self.service, key, value)

    def get(self, key: str) -> Optional[str]:
        return self._keyring.get_password(self.service, key)


class NoopSecretStore(SecretStore):
    """Does not persist secrets; used if keyring cannot be used."""

    def __init__(self):
        self._mem: dict[str, str] = {}

    def set(self, key: str, value: str) -> None:
        self._mem[key] = value

    def get(self, key: str) -> Optional[str]:
        return self._mem.get(key)


_store: SecretStore | None = None


def get_secret_store() -> SecretStore:
    global _store
    if _store is not None:
        return _store

    try:
        _store = KeyringSecretStore()
    except Exception:
        _store = NoopSecretStore()
    return _store

