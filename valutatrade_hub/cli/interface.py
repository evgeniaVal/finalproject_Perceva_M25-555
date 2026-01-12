from argparse import ArgumentParser
from shlex import split as shlex_split

from prompt import string as prompt_string


class MyArgumentParser(ArgumentParser):
    def error(self, message: str):
        raise ValueError(message)


def build_parser() -> ArgumentParser:
    parser = MyArgumentParser(prog="valutatrade", add_help=False)

    sub = parser.add_subparsers(dest="command", required=True)

    p_exit = sub.add_parser("exit", aliases=["quit", "q"], add_help=False)
    p_exit.set_defaults(command="exit")

    p_register = sub.add_parser("register", add_help=False)
    p_register.add_argument("--username", type=str, required=True)
    p_register.add_argument("--password", type=str, required=True)

    return parser


def get_input(prompt_msg="> "):
    try:
        input_str = prompt_string(prompt_msg).strip()  # type: ignore
        tokens = shlex_split(input_str) or []
    except (KeyboardInterrupt, EOFError):
        tokens = ["exit"]
    return tokens


def process_command(parser, tokens):
    try:
        ns = parser.parse_args(tokens)
    except ValueError:
        print(f"Неизвестная команда: {tokens[0]}")
        return True
    match ns.command:
        case "exit":
            print("До свидания!")
            return False
        case "register":
            print("Parsed args:", ns)
            return True
        case _:
            print(f"Неизвестная команда: {ns.command}")
            return True


def main():
    parser = build_parser()
    print("Приветствие!")
    while process_command(parser, get_input()):
        pass


if __name__ == "__main__":
    main()
