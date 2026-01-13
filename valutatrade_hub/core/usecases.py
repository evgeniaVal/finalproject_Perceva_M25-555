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
    lines = [f"Портфель пользователя '{username}' (база: {base_cur}):"]
    if not portfolio.wallets:
        lines.append("Кошельков пока нет.")
        lines.append("---------------------------------")
        lines.append(f"ИТОГО: 0.00 {base_cur}")
        return "\n".join(lines)
    total = 0.0
    for code in portfolio.wallets.keys():
        wallet = portfolio.get_wallet(code)
        amount = float(wallet.balance)

        try:
            rate = portfolio.get_rate(code, base_cur)
        except ValueError:
            raise ValueError(f"Неизвестная базовая валюта '{base_cur}'")
        value_in_base = amount * rate
        total += value_in_base

        amt_str = f"{amount:.2f}"
        val_str = f"{value_in_base:,.2f}"

        lines.append(f"- {code}: {amt_str}  → {val_str} {base_cur}")

    total_str = f"{total:,.2f}"

    lines.append("---------------------------------")
    lines.append(f"ИТОГО: {total_str} {base_cur}")

    return "\n".join(lines)
