from datetime import datetime
from hashlib import sha256
from secrets import token_hex


class User:
    _user_id: int  # уникальный идентификатор пользователя
    _username: str  # имя пользователя
    _hashed_password: str  # пароль в зашифрованном виде
    _salt: str  # уникальная соль для пользователя
    _registration_date: datetime  # дата регистрации пользователя

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, new_username: str) -> None:
        if (
            not new_username
            or not isinstance(new_username, str)
            or new_username.strip() == ""
        ):
            raise ValueError("Username must be a non-empty string.")
        self._username = new_username.strip()

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime,
    ):
        if not user_id or not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("User ID must be a positive integer.")
        self._user_id = user_id
        self.username = username
        if (
            not hashed_password
            or not isinstance(hashed_password, str)
            or hashed_password.strip() == ""
        ):
            raise ValueError("Hashed password must be a non-empty string.")
        self._hashed_password = hashed_password
        if not salt or not isinstance(salt, str) or salt.strip() == "":
            raise ValueError("Salt must be a non-empty string.")
        self._salt = salt
        if not isinstance(registration_date, datetime):
            raise ValueError("Registration date must be a datetime object.")
        self._registration_date = registration_date

    def get_user_info(self) -> dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "registration_date": self.registration_date.isoformat(),
        }

    def change_password(self, new_password: str) -> None:
        if (
            not new_password
            or not isinstance(new_password, str)
            or len(new_password) < 4
        ):
            raise ValueError("Password must be at least 4 characters long.")
        self._salt = token_hex(16)
        self._hashed_password = sha256(
            (new_password + self._salt).encode("utf-8")
        ).hexdigest()

    def verify_password(self, password: str) -> bool:
        if not password or not isinstance(password, str):
            return False
        hashed_input = sha256((password + self._salt).encode("utf-8")).hexdigest()
        return hashed_input == self._hashed_password


class Wallet:
    currency_code: str  # код валюты (например, "USD", "BTC")
    _balance: float  # баланс в данной валюте (по умолчанию 0.0)

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, new_balance: int | float) -> None:
        if not isinstance(new_balance, (int, float)) or new_balance < 0:
            raise ValueError("Balance must be a non-negative number.")
        self._balance = float(new_balance)

    def __init__(self, currency_code: str, initial_balance: int | float = 0.0):
        if (
            not currency_code
            or not isinstance(currency_code, str)
            or currency_code.strip() == ""
            or not currency_code.strip().isupper()
        ):
            raise ValueError("Currency code must be a non-empty uppercase string.")
        self.currency_code = currency_code
        self.balance = float(initial_balance)

    def deposit(self, amount: float) -> None:
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount

    def withdraw(self, amount: float) -> None:
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if amount > self.balance:
            raise ValueError("Insufficient funds for withdrawal.")
        self.balance -= amount

    def get_balance_info(self) -> dict:
        return {
            "currency_code": self.currency_code,
            "balance": self.balance,
        }
