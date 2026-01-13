from argparse import ArgumentParser
from functools import wraps
from shlex import split as shlex_split

from prompt import string as prompt_string

from valutatrade_hub.core.usecases import buy, login, register, show_portfolio


def format_buy_result(data: dict) -> str:
    lines = []
    lines.append(
        f"Покупка выполнена: {data['amount']:.4f} {data['currency']} "
        f"по курсу {data['rate']:,.2f} {data['base_currency']}/{data['currency']}"
    )
    lines.append("Изменения в портфеле:")
    lines.append(
        f"- {data['currency']}: было {data['old_balance']:.4f} → "
        f"стало {data['new_balance']:.4f}"
    )
    lines.append(
        f"Оценочная стоимость покупки: {data['cost']:,.2f} {data['base_currency']}"
    )
    return "\n".join(lines)


def format_portfolio_result(data: dict) -> str:
    lines = [
        f"Портфель пользователя '{data['username']}' (база: {data['base_currency']}):"
    ]

    if not data["wallets"]:
        lines.append("Кошельков пока нет.")
        lines.append("---------------------------------")
        lines.append(f"ИТОГО: 0.00 {data['base_currency']}")
        return "\n".join(lines)

    for wallet in data["wallets"]:
        amt_str = f"{wallet['amount']:.2f}"
        val_str = f"{wallet['value_in_base']:,.2f}"
        lines.append(
            f"- {wallet['currency']}: {amt_str}\t→\t{val_str} {data['base_currency']}"
        )

    total_str = f"{data['total']:,.2f}"
    lines.append("---------------------------------")
    lines.append(f"ИТОГО: {total_str} {data['base_currency']}")

    return "\n".join(lines)


def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(e)

    return wrapper


buy = handle_errors(buy)
login = handle_errors(login)
register = handle_errors(register)
show_portfolio = handle_errors(show_portfolio)


def check_login(login_id):
    if login_id is None or not isinstance(login_id, int) or login_id <= 0:
        print("Сначала выполните login.")
        return False
    return True


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

    p_show_portfolio = sub.add_parser("show-portfolio", add_help=False)
    p_show_portfolio.add_argument(
        "-b", "--base", type=str, default="USD", required=False
    )
    p_show_portfolio.set_defaults(command="show-portfolio")

    p_buy = sub.add_parser("buy", add_help=False)
    p_buy.add_argument("-c", "--currency", type=str, required=True)
    p_buy.add_argument("-a", "--amount", type=float, required=True)
    p_buy.set_defaults(command="buy")

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
        case "show-portfolio":
            if not check_login(logged_id):
                return logged_id, True
            data = show_portfolio(logged_id, ns.base)
            if data:
                print(format_portfolio_result(data))
            return logged_id, True
        case "buy":
            if not check_login(logged_id):
                return logged_id, True
            result = buy(logged_id, ns.currency, ns.amount)
            if result:
                print(format_buy_result(result))
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
