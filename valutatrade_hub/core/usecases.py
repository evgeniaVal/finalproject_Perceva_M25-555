from .currencies import get_currency
from .models import Portfolio, User
from .utils import load_json, save_json

USERS_LOC = "data/users.json"
PORTFOLIOS_LOC = "data/portfolios.json"
BASE_CURRENCY = "USD"


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
    user = _get_user(user_id)
    username = user.get("username", "")
    portfolio, _, _ = _get_portfolio(user_id)
    base_cur = base.strip().upper() if isinstance(base, str) else "USD"
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
    _get_user(user_id)
    currency_code = get_currency(currency).code

    portfolio, portfolio_index, portfolios = _get_portfolio(user_id)

    if currency_code not in portfolio.wallets:
        portfolio.add_currency(currency_code)
    wallet = portfolio.get_wallet(currency_code)
    old_balance = wallet.balance
    wallet.deposit(amount)
    new_balance = wallet.balance

    rate = Portfolio.get_rate(currency_code, BASE_CURRENCY)
    cost = amount * rate

    portfolios[portfolio_index] = Portfolio.to_dict(portfolio)
    save_json(PORTFOLIOS_LOC, portfolios)

    return {
        "currency": currency_code,
        "amount": amount,
        "rate": rate,
        "base_currency": BASE_CURRENCY,
        "old_balance": old_balance,
        "new_balance": new_balance,
        "cost": cost,
    }


def sell(user_id: int, currency: str, amount: float):
    _get_user(user_id)
    currency_code = get_currency(currency).code

    portfolio, portfolio_index, portfolios = _get_portfolio(user_id)

    if currency_code not in portfolio.wallets:
        raise ValueError(
            f"У вас нет кошелька {currency_code}. Добавьте валюту."
            " Она создаётся автоматически при первой покупке."
        )
    wallet = portfolio.get_wallet(currency_code)
    old_balance = wallet.balance
    wallet.withdraw(amount)
    new_balance = wallet.balance

    rate = Portfolio.get_rate(currency_code, BASE_CURRENCY)
    cost = amount * rate

    portfolios[portfolio_index] = Portfolio.to_dict(portfolio)
    save_json(PORTFOLIOS_LOC, portfolios)

    return {
        "currency": currency_code,
        "amount": amount,
        "rate": rate,
        "base_currency": BASE_CURRENCY,
        "old_balance": old_balance,
        "new_balance": new_balance,
        "cost": cost,
    }


def get_rate(from_cur: str, to_cur: str) -> dict:
    from_currency_obj = get_currency(from_cur)
    to_currency_obj = get_currency(to_cur)
    from_code = from_currency_obj.code
    to_code = to_currency_obj.code

    rate = Portfolio.get_rate(from_code, to_code)
    reverse_rate = 1.0 / rate if rate != 0 else 0.0

    pair = f"{from_code}_{to_code}"
    reverse_pair = f"{to_code}_{from_code}"

    rec = Portfolio.EXCHANGE_RATES.get(pair) or Portfolio.EXCHANGE_RATES.get(
        reverse_pair
    )
    updated_at = rec.get("updated_at") if isinstance(rec, dict) else None

    return {
        "from_currency": from_code,
        "to_currency": to_code,
        "rate": rate,
        "reverse_rate": reverse_rate,
        "updated_at": updated_at,
    }
