from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader

from .currencies import get_currency
from .models import Portfolio, User

_db = DatabaseManager()
_settings = SettingsLoader()


def _find_by_id(items: list[dict], user_id: int, item_name: str) -> tuple[dict, int]:
    for idx, item in enumerate(items):
        if int(item.get("user_id", -1)) == int(user_id):
            return item, idx
    raise ValueError(f"{item_name} с id={user_id} не найден.")


def _get_user(user_id: int) -> dict:
    """Возвращает пользователя по id."""
    users = _db.load_users()
    user, _ = _find_by_id(users, user_id, "Пользователь")
    return user


def _get_portfolio(user_id: int):
    portfolios = _db.load_portfolios()
    portfolio_dict, idx = _find_by_id(portfolios, user_id, "Портфель пользователя")
    return Portfolio.from_dict(portfolio_dict), idx, portfolios


@log_action(action_name="REGISTER")
def register(username: str, password: str) -> dict:
    uname = username.strip()
    users = _db.load_users()
    if any(u["username"] == uname for u in users):
        raise ValueError(f"Имя пользователя '{uname}' уже занято.")
    new_id = max((u["user_id"] for u in users), default=0) + 1
    new_user = User.from_plain_password(new_id, uname, password)
    users.append(User.to_dict(new_user))
    _db.save_users(users)
    new_portfolio = Portfolio(new_id, {})
    portfolios = _db.load_portfolios()
    portfolios.append(Portfolio.to_dict(new_portfolio))
    _db.save_portfolios(portfolios)
    return {"user_id": new_id, "username": uname}


@log_action(action_name="LOGIN")
def login(username: str, password: str) -> dict:
    uname = username.strip()
    users = _db.load_users()
    for u in users:
        if u["username"] == uname:
            user = User.from_dict(u)
            if user.verify_password(password):
                return {"user_id": user.user_id, "username": uname}
            else:
                raise ValueError("Неверный пароль.")
    raise ValueError(f"Пользователь '{uname}' не найден.")


def show_portfolio(user_id: int, base: str):
    user = _get_user(user_id)
    username = user.get("username", "")
    portfolio, _, _ = _get_portfolio(user_id)
    base_cur = (
        base.strip().upper()
        if isinstance(base, str) and base.strip()
        else _settings.base_currency
    )
    wallets_info = []
    total = 0.0
    for code, wallet in portfolio.wallets.items():
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


def _execute_trade(
    user_id: int,
    currency: str,
    amount: float,
    operation: str,
) -> dict:
    user = _get_user(user_id)
    username = user.get("username", "")
    currency_code = get_currency(currency).code

    portfolio, portfolio_index, portfolios = _get_portfolio(user_id)

    if currency_code not in portfolio.wallets:
        if operation == "sell":
            raise ValueError(
                f"У вас нет кошелька {currency_code}. Добавьте валюту."
                " Она создаётся автоматически при первой покупке."
            )
        portfolio.add_currency(currency_code)
    wallet = portfolio.get_wallet(currency_code)
    old_balance = wallet.balance
    if operation == "buy":
        wallet.deposit(amount)
    else:
        wallet.withdraw(amount)
    new_balance = wallet.balance

    rate = Portfolio.get_rate(currency_code, _settings.base_currency)
    cost = amount * rate

    portfolios[portfolio_index] = Portfolio.to_dict(portfolio)
    _db.save_portfolios(portfolios)

    return {
        "username": username,
        "currency": currency_code,
        "amount": amount,
        "rate": rate,
        "base_currency": _settings.base_currency,
        "old_balance": old_balance,
        "new_balance": new_balance,
        "cost": cost,
    }


@log_action(action_name="BUY", verbose=True)
def buy(user_id: int, currency: str, amount: float):
    return _execute_trade(user_id, currency, amount, "buy")


@log_action(action_name="SELL", verbose=True)
def sell(user_id: int, currency: str, amount: float):
    return _execute_trade(user_id, currency, amount, "sell")


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
