from .models import Portfolio, User
from .utils import load_json, save_json

USERS_LOC = "data/users.json"
PORTFOLIOS_LOC = "data/portfolios.json"


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
    users = load_json(USERS_LOC, default=list)
    username = None
    for u in users:
        if int(u.get("user_id", -1)) == int(user_id):
            username = str(u.get("username", ""))
            break
    if not username:
        raise ValueError(f"Пользователь с id={user_id} не найден.")
    portfolios = load_json(PORTFOLIOS_LOC, default=list)
    found = None
    for p in portfolios:
        if int(p.get("user_id", -1)) == int(user_id):
            found = p
            break
    if found is None:
        raise ValueError(f"Портфель пользователя с id={user_id} не найден.")
    portfolio = Portfolio.from_dict(found)
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

        wallets_info.append({
            "currency": code,
            "amount": amount,
            "rate": rate,
            "value_in_base": value_in_base,
        })

    return {
        "username": username,
        "base_currency": base_cur,
        "wallets": wallets_info,
        "total": total,
    }


def buy(user_id: int, currency: str, amount: float):
    users = load_json(USERS_LOC, default=list)
    user_found = False
    for u in users:
        if int(u.get("user_id", -1)) == int(user_id):
            user_found = True
            break
    if not user_found:
        raise ValueError(f"Пользователь с id={user_id} не найден.")
    if not isinstance(currency, str) or not currency.strip():
        raise ValueError("currency должен быть непустой строкой.")
    currency_code = currency.strip().upper()
    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError("'amount' должен быть положительным числом.")
    base_cur = "USD"
    portfolios = load_json(PORTFOLIOS_LOC, default=list)
    portfolio_data = None
    portfolio_index = None
    for idx, p in enumerate(portfolios):
        if int(p.get("user_id", -1)) == int(user_id):
            portfolio_data = p
            portfolio_index = idx
            break
    if portfolio_data is None:
        raise ValueError(f"Портфель пользователя с id={user_id} не найден.")
    portfolio = Portfolio.from_dict(portfolio_data)
    if currency_code not in portfolio.wallets:
        portfolio.add_currency(currency_code)
    wallet = portfolio.get_wallet(currency_code)
    old_balance = portfolio.get_wallet(currency_code).balance
    wallet.deposit(amount)
    new_balance = wallet.balance
    try:
        rate = Portfolio.get_rate(currency_code, base_cur)
    except ValueError:
        raise ValueError(f"Не удалось получить курс для {currency_code}→{base_cur}")

    cost = amount * rate

    if portfolio_index is None:
        raise ValueError(f"Портфель пользователя с id={user_id} не найден.")
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
