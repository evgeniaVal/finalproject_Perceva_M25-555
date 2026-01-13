from .models import Portfolio, User
from .utils import load_json, save_json

USERS_LOC = "data/users.json"
PORTFOLIOS_LOC = "data/portfolios.json"


def _get_user(user_id: int) -> dict:
    """Возвращает пользователя по id."""
    users = load_json(USERS_LOC, default=list)
    for u in users:
        if int(u.get("user_id", -1)) == int(user_id):
            return u
    raise ValueError(f"Пользователь с id={user_id} не найден.")


def _get_portfolio(user_id: int):
    portfolios = load_json(PORTFOLIOS_LOC, default=list)
    for idx, p in enumerate(portfolios):
        if int(p.get("user_id", -1)) == int(user_id):
            return Portfolio.from_dict(p), idx, portfolios
    raise ValueError(f"Портфель пользователя с id={user_id} не найден.")


def _validate_currency(currency: str) -> str:
    if not isinstance(currency, str) or not currency.strip():
        raise ValueError("currency должен быть непустой строкой.")
    return currency.strip().upper()


def _validate_amount(amount: float):
    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError("'amount' должен быть положительным числом.")


def _get_rate(currency_code: str, base_cur: str) -> float:
    try:
        return Portfolio.get_rate(currency_code, base_cur)
    except ValueError:
        raise ValueError(f"Не удалось получить курс для {currency_code}→{base_cur}")


def register(username: str, password: str):
    uname = username.strip()
    users = load_json(USERS_LOC, default=list)
    if any(u["username"] == uname for u in users):
        raise ValueError(f"Имя пользователя '{uname}' уже занято.")
    new_id = max((u["user_id"] for u in users), default=0) + 1
    new_user = User.from_plain_password(new_id, uname, password)
    users.append(User.to_dict(new_user))
    save_json(USERS_LOC, users)
    new_portfolio = Portfolio(new_id, {})
    portfolios = load_json(PORTFOLIOS_LOC, default=list)
    portfolios.append(Portfolio.to_dict(new_portfolio))
    save_json(PORTFOLIOS_LOC, portfolios)
    return new_id


def login(username: str, password: str) -> int:
    uname = username.strip()
    users = load_json(USERS_LOC, default=list)
    for u in users:
        if u["username"] == uname:
            user = User.from_dict(u)
            if user.verify_password(password):
                return user.user_id
            else:
                raise ValueError("Неверный пароль.")
    raise ValueError(f"Пользователь '{uname}' не найден.")


def show_portfolio(user_id: int, base: str):
    if not isinstance(base, str) or not base.strip():
        raise ValueError("base_currency must be a non-empty string.")
    base_cur = base.strip().upper()
    user = _get_user(user_id)
    username = user.get("username", "")
    portfolio, _, _ = _get_portfolio(user_id)
    wallets_info = []
    total = 0.0
    for code in portfolio.wallets.keys():
        wallet = portfolio.get_wallet(code)
        amount = float(wallet.balance)

        try:
            rate = Portfolio.get_rate(code, base_cur)
        except ValueError:
            raise ValueError(f"Неизвестная базовая валюта '{base_cur}'")
        value_in_base = amount * rate
        total += value_in_base

        wallets_info.append(
            {
                "currency": code,
                "amount": amount,
                "rate": rate,
                "value_in_base": value_in_base,
            }
        )

    return {
        "username": username,
        "base_currency": base_cur,
        "wallets": wallets_info,
        "total": total,
    }


def buy(user_id: int, currency: str, amount: float):
    base_cur = "USD"

    _get_user(user_id)
    currency_code = _validate_currency(currency)
    _validate_amount(amount)

    portfolio, portfolio_index, portfolios = _get_portfolio(user_id)

    if currency_code not in portfolio.wallets:
        portfolio.add_currency(currency_code)
    wallet = portfolio.get_wallet(currency_code)
    old_balance = wallet.balance
    wallet.deposit(amount)
    new_balance = wallet.balance

    rate = _get_rate(currency_code, base_cur)
    cost = amount * rate

    portfolios[portfolio_index] = Portfolio.to_dict(portfolio)
    save_json(PORTFOLIOS_LOC, portfolios)

    return {
        "currency": currency_code,
        "amount": amount,
        "rate": rate,
        "base_currency": base_cur,
        "old_balance": old_balance,
        "new_balance": new_balance,
        "cost": cost,
    }


def sell(user_id: int, currency: str, amount: float):
    base_cur = "USD"

    _get_user(user_id)
    currency_code = _validate_currency(currency)
    _validate_amount(amount)

    portfolio, portfolio_index, portfolios = _get_portfolio(user_id)

    if currency_code not in portfolio.wallets:
        raise ValueError(
            f"У вас нет кошелька {currency_code}. Добавьте валюту."
            " Она создаётся автоматически при первой покупке."
        )
    wallet = portfolio.get_wallet(currency_code)
    old_balance = wallet.balance
    try:
        wallet.withdraw(amount)
    except ValueError:
        raise ValueError(
            f"Недостаточно средств: доступно {wallet.balance} {currency_code},"
            f" требуется {amount} {currency_code}"
        )
    new_balance = wallet.balance

    rate = _get_rate(currency_code, base_cur)
    cost = amount * rate

    portfolios[portfolio_index] = Portfolio.to_dict(portfolio)
    save_json(PORTFOLIOS_LOC, portfolios)

    return {
        "currency": currency_code,
        "amount": amount,
        "rate": rate,
        "base_currency": base_cur,
        "old_balance": old_balance,
        "new_balance": new_balance,
        "cost": cost,
    }
