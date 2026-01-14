from datetime import datetime, timezone
from hashlib import sha256
from secrets import token_hex

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import InsufficientFundsError


class User:
    """Пользователь системы валютного кошелька.

    Attributes:
        _user_id (int): Уникальный идентификатор пользователя.
        _username (str): Имя пользователя.
        _hashed_password (str): Хешированный пароль.
        _salt (str): Соль для хеширования пароля.
        _registration_date (datetime): Дата и время регистрации.
    """

    _user_id: int
    _username: str
    _hashed_password: str
    _salt: str
    _registration_date: datetime

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, new_username: str) -> None:
        if not isinstance(new_username, str) or not new_username.strip():
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

    @staticmethod
    def to_dict(user: "User") -> dict:
        """Преобразует объект User в словарь для сериализации.

        Args:
            user (User): Объект пользователя для преобразования.

        Returns:
            dict: Словарь с данными пользователя.
        """
        return {
            "user_id": user.user_id,
            "username": user.username,
            "hashed_password": user.hashed_password,
            "salt": user.salt,
            "registration_date": user.registration_date.isoformat(),
        }

    @staticmethod
    def from_dict(data: dict) -> "User":
        """Создает объект User из словаря.

        Args:
            data (dict): Словарь с данными пользователя.

        Raises:
            ValueError: Если данные невалидны или отсутствуют обязательные поля.

        Returns:
            User: Объект пользователя.
        """
        try:
            return User(
                user_id=int(data["user_id"]),
                username=str(data["username"]),
                hashed_password=str(data["hashed_password"]),
                salt=str(data["salt"]),
                registration_date=datetime.fromisoformat(
                    str(data["registration_date"])
                ),
            )
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError(f"Invalid user data: {e}")

    @staticmethod
    def _verify_password_format(password: str) -> None:
        if not isinstance(password, str) or len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов.")

    @staticmethod
    def _create_hash(password: str, salt: str) -> str:
        if not isinstance(password, str) or not isinstance(salt, str):
            raise ValueError("Password and salt must be strings.")
        return sha256((password + salt).encode("utf-8")).hexdigest()

    @staticmethod
    def _hash_password(password: str) -> tuple[str, str]:
        User._verify_password_format(password)
        salt = token_hex(16)
        hashed = User._create_hash(password, salt)
        return hashed, salt

    @staticmethod
    def from_plain_password(user_id: int, username: str, password: str) -> "User":
        """Создает нового пользователя с незашифрованным паролем.

        Args:
            user_id (int): Уникальный идентификатор пользователя.
            username (str): Имя пользователя.
            password (str): Пароль в открытом виде.

        Raises:
            ValueError: Если пароль слишком короткий (< 4 символов).

        Returns:
            User: Новый объект пользователя с захешированным паролем.
        """
        hashed, salt = User._hash_password(password)
        return User(
            user_id=user_id,
            username=username,
            hashed_password=hashed,
            salt=salt,
            registration_date=datetime.now(timezone.utc),
        )

    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime,
    ) -> None:
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("User ID must be a positive integer.")
        self._user_id = user_id
        self.username = username
        if not isinstance(hashed_password, str) or not hashed_password.strip():
            raise ValueError("Hashed password must be a non-empty string.")
        self._hashed_password = hashed_password
        if not isinstance(salt, str) or not salt.strip():
            raise ValueError("Salt must be a non-empty string.")
        self._salt = salt
        if not isinstance(registration_date, datetime):
            raise ValueError("Registration date must be a datetime object.")
        self._registration_date = registration_date

    def get_user_info(self) -> dict:
        """Возвращает публичную информацию о пользователе.

        Returns:
            dict: Словарь с user_id, username и registration_date (без пароля).
        """
        return {
            "user_id": self.user_id,
            "username": self.username,
            "registration_date": self.registration_date.isoformat(),
        }

    def change_password(self, new_password: str) -> None:
        """Изменяет пароль пользователя.

        Args:
            new_password (str): Новый пароль в открытом виде.

        Raises:
            ValueError: Если новый пароль не соответствует требованиям (< 4 символов).
        """
        User._verify_password_format(new_password)
        self._hashed_password, self._salt = User._hash_password(new_password)

    def verify_password(self, password: str) -> bool:
        """Проверяет соответствие введенного пароля сохраненному хешу.

        Args:
            password (str): Пароль для проверки.

        Returns:
            bool: True, если пароль верный, False в противном случае.
        """
        if not isinstance(password, str) or not password:
            return False
        return User._create_hash(password, self._salt) == self._hashed_password


class Wallet:
    """Кошелек для хранения баланса одной валюты.

    Attributes:
        currency_code (str): Код валюты (например, USD, BTC).
        _balance (float): Текущий баланс в данной валюте.
    """

    currency_code: str
    _balance: float

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, new_balance: int | float) -> None:
        if not isinstance(new_balance, (int, float)) or new_balance < 0:
            raise ValueError("Balance must be a non-negative number.")
        self._balance = float(new_balance)

    def __init__(self, currency_code: str, initial_balance: int | float = 0.0) -> None:
        if (
            not isinstance(currency_code, str)
            or not currency_code.strip()
            or not currency_code.strip().isupper()
        ):
            raise ValueError("Currency code must be a non-empty uppercase string.")
        self.currency_code = currency_code.strip()
        self.balance = float(initial_balance)

    def deposit(self, amount: float) -> None:
        """Пополняет баланс кошелька.

        Args:
            amount (float): Сумма пополнения.

        Raises:
            ValueError: Если сумма не положительная.
        """
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount

    def withdraw(self, amount: float) -> None:
        """Снимает средства с кошелька.

        Args:
            amount (float): Сумма снятия.

        Raises:
            ValueError: Если сумма не положительная.
            InsufficientFundsError: Если на балансе недостаточно средств.
        """
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if amount > self.balance:
            raise InsufficientFundsError(
                available=self.balance,
                required=amount,
                currency_code=self.currency_code,
            )
        self.balance -= amount

    def get_balance_info(self):
        """Возвращает информацию о балансе кошелька.

        Returns:
            dict: Словарь с currency_code и balance.
        """
        return {
            "currency_code": self.currency_code,
            "balance": self.balance,
        }


class Portfolio:
    """Портфель пользователя, содержащий все его кошельки.

    Attributes:
        _user_id (int): Идентификатор владельца портфеля.
        _wallets (dict[str, Wallet]): Словарь кошельков, где ключ - код валюты.
    """

    _user_id: int
    _wallets: dict[str, Wallet]
    EXCHANGE_RATES: dict = {}

    def __init__(self, user_id: int, wallets: dict[str, Wallet]) -> None:
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("User ID must be a positive integer.")
        self._user_id = user_id
        self._wallets = {}
        if wallets is None:
            wallets = {}
        if not isinstance(wallets, dict):
            raise ValueError("Wallets must be provided as a dictionary.")

        for code, wallet in wallets.items():
            self._wallets[code] = wallet

    @property
    def user(self):
        raise NotImplementedError("Property user is not implemented yet.")

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> dict[str, Wallet]:
        return self._wallets.copy()

    @staticmethod
    def to_dict(portfolio: "Portfolio") -> dict:
        return {
            "user_id": portfolio.user_id,
            "wallets": {
                code: {"balance": wallet.balance}
                for code, wallet in portfolio.wallets.items()
            },
        }

    @staticmethod
    def from_dict(data: dict) -> "Portfolio":
        try:
            wallets_data = data.get("wallets", {})
            wallets = {
                code: Wallet(currency_code=code, initial_balance=float(info["balance"]))
                for code, info in wallets_data.items()
            }
            return Portfolio(
                user_id=int(data["user_id"]),
                wallets=wallets,
            )
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError(f"Invalid portfolio data: {e}")

    def add_currency(self, currency_code: str) -> None:
        """Добавляет новый кошелек для указанной валюты.

        Args:
            currency_code (str): Код валюты для добавления.

        Raises:
            CurrencyNotFoundError: Если валюта не найдена в реестре.
            ValueError: Если валюта уже существует в портфеле.
        """
        currency = get_currency(currency_code)
        code = currency.code

        if code in self._wallets:
            raise ValueError(f"Currency '{code}' already exists in the portfolio.")

        self._wallets[code] = Wallet(code)

    def get_wallet(self, currency_code: str) -> Wallet:
        """Возвращает кошелек для указанной валюты.

        Args:
            currency_code (str): Код валюты.

        Raises:
            CurrencyNotFoundError: Если валюта не найдена в реестре.
            ValueError: Если кошелек для валюты не существует в портфеле.

        Returns:
            Wallet: Объект кошелька.
        """
        currency = get_currency(currency_code)
        code = currency.code

        if code not in self._wallets:
            raise ValueError(f"Currency '{code}' not found in the portfolio.")

        return self._wallets[code]

    @staticmethod
    def get_rate(from_cur: str, to_cur: str) -> float:
        """Получает курс обмена между двумя валютами.

        Args:
            from_cur (str): Код исходной валюты.
            to_cur (str): Код целевой валюты.

        Raises:
            ValueError: Если курс не найден или невалиден.

        Returns:
            float: Курс обмена (1 единица from_cur = rate единиц to_cur).
        """
        if from_cur == to_cur:
            return 1.0
        pair = f"{from_cur}_{to_cur}"
        rec = Portfolio.EXCHANGE_RATES.get(pair)
        if isinstance(rec, dict) and "rate" in rec:
            rate = rec["rate"]
            if not isinstance(rate, (int, float)) or rate <= 0:
                raise ValueError(
                    f"Invalid exchange rate for pair '{from_cur}' to '{to_cur}': {rate}"
                )
            return float(rate)
        reverse_pair = f"{to_cur}_{from_cur}"
        rec = Portfolio.EXCHANGE_RATES.get(reverse_pair)
        if isinstance(rec, dict) and "rate" in rec:
            rate = rec["rate"]
            if not isinstance(rate, (int, float)) or rate <= 0:
                raise ValueError(
                    f"Invalid exchange rate for pair '{to_cur}' to '{from_cur}': {rate}"
                )
            return 1.0 / float(rate)
        if from_cur != "USD" and to_cur != "USD":
            try:
                from_to_usd = Portfolio.get_rate(from_cur, "USD")
                usd_to_target = Portfolio.get_rate("USD", to_cur)
                return from_to_usd * usd_to_target
            except ValueError:
                pass
        raise ValueError(
            f"Exchange rate for pair '{from_cur}' to '{to_cur}' not found."
        )

    def get_total_value(self, base_currency: str = "USD") -> float:
        """Вычисляет общую стоимость всех кошельков в указанной валюте.

        Args:
            base_currency (str): Базовая валюта для расчета (по умолчанию USD).

        Raises:
            ValueError: Если base_currency невалидна или курс не найден.

        Returns:
            float: Общая стоимость портфеля в базовой валюте.
        """
        if not isinstance(base_currency, str) or not base_currency.strip():
            raise ValueError("base_currency must be a non-empty string.")
        base = base_currency.strip().upper()

        total_in_base = 0.0
        for code, wallet in self._wallets.items():
            cur = code.upper()
            amount = float(wallet.balance)

            if amount == 0.0:
                continue

            rate = Portfolio.get_rate(cur, base)
            total_in_base += amount * rate

        return total_in_base
