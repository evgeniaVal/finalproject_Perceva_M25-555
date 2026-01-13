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
