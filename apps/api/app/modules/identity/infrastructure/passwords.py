from argon2 import PasswordHasher as _Argon2
from argon2.exceptions import InvalidHashError, VerifyMismatchError


class Argon2Hasher:
    def __init__(self) -> None:
        self._h = _Argon2()

    def hash(self, password: str) -> str:
        return self._h.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        try:
            return self._h.verify(hashed, password)
        except (VerifyMismatchError, InvalidHashError):
            return False
