from argparse import ArgumentParser
from functools import wraps
from shlex import split as shlex_split

from prompt import string as prompt_string

from valutatrade_hub.core.usecases import login, register


def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(e)

    return wrapper


login = handle_errors(login)
register = handle_errors(register)


class MyArgumentParser(ArgumentParser):
    def error(self, message: str):
        raise ValueError(message)


def build_parser() -> ArgumentParser:
    parser = MyArgumentParser(prog="valutatrade", add_help=False)

    sub = parser.add_subparsers(dest="command", required=True)

    p_exit = sub.add_parser("exit", aliases=["quit", "q"], add_help=False)
    p_exit.set_defaults(command="exit")

    p_register = sub.add_parser("register", add_help=False)
    p_register.add_argument("-u", "--username", type=str, required=True)
    p_register.add_argument("-p", "--password", type=str, required=True)
    p_register.set_defaults(command="register")

    p_login = sub.add_parser("login", add_help=False)
    p_login.add_argument("-u", "--username", type=str, required=True)
    p_login.add_argument("-p", "--password", type=str, required=True)
    p_login.set_defaults(command="login")

    return parser


def get_input(prompt_msg="> "):
    try:
        input_str = prompt_string(prompt_msg).strip()  # type: ignore
        tokens = shlex_split(input_str) or []
    except (KeyboardInterrupt, EOFError):
        tokens = ["exit"]
    return tokens


def process_command(logged_id, parser, tokens):
    try:
        ns = parser.parse_args(tokens)
    except ValueError:
        print(f"Неизвестная команда: {' '.join(tokens)}")
        return logged_id, True
    match ns.command:
        case "exit":
            print("До свидания!")
            return logged_id, False
        case "register":
            idx = register(ns.username, ns.password)
            if idx:
                print(
                    f"Пользователь '{ns.username}' успешно зарегистрирован (id={idx})."
                    f" Войдите: login --username {ns.username} --password ****"
                )
            return logged_id, True
        case "login":
            new_id = login(ns.username, ns.password)
            if new_id:
                print(f"Вы вошли как '{ns.username}'.")
                return new_id, True
            return logged_id, True
        case _:
            return logged_id, True


def main():
    parser = build_parser()
    print("Приветствие!")
    not_over = True
    logged_id = None
    while not_over:
        logged_id, not_over = process_command(logged_id, parser, get_input())


if __name__ == "__main__":
    main()
