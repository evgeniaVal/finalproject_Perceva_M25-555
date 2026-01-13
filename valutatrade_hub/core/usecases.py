from .models import User
from .utils import load_json, save_json

USERS_LOC = "data/users.json"


def register(username: str, password: str):
    users = load_json(USERS_LOC, default=list)
    if any(u["username"] == username for u in users):
        raise ValueError(f"Имя пользователя '{username}' уже занято.")
    new_id = max((u["user_id"] for u in users), default=0) + 1
    new_user = User.from_plain_password(new_id, username, password)
    users.append(User.to_dict(new_user))
    save_json(USERS_LOC, users)
    return new_id
