from datetime import datetime
from hashlib import sha256
from secrets import token_hex


class User:
    _user_id: int  # уникальный идентификатор пользователя
    _username: str  # имя пользователя
    _hashed_password: str  # пароль в зашифрованном виде
    _salt: str  # уникальная соль для пользователя
    _registration_date: datetime  # дата регистрации пользователя

    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime,
    ):
        self._user_id = user_id
        self._username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, new_username: str) -> None:
        if not new_username:
            raise ValueError("Username cannot be empty.")
        self._username = new_username

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    def get_user_info(self) -> dict:
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def change_password(self, new_password: str) -> None:
        if len(new_password) < 4:
            raise ValueError("Password must be at least 4 characters long.")
        self._salt = token_hex(16)
        self._hashed_password = sha256(
            (new_password + self._salt).encode("utf-8")
        ).hexdigest()

    def verify_password(self, password: str) -> bool:
        hashed_input = sha256((password + self._salt).encode("utf-8")).hexdigest()
        return hashed_input == self._hashed_password
