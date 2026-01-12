from shlex import split as shlex_split

from prompt import string as prompt_string


def get_input(prompt_msg="> "):
    try:
        input_str = prompt_string(prompt_msg).strip()  # type: ignore
        args = shlex_split(input_str)
    except (KeyboardInterrupt, EOFError):
        args = ["exit"]
    return args[0].lower(), args[1:]


def process_command(command, args):
    match command:
        case "exit" | "quit":
            print("Выход из ValutaTrade Hub CLI. До свидания!")
            return False
        case _:
            print(f"Неизвестная команда: {command}")
    return True


def main():
    print("Приветствие в ValutaTrade Hub CLI!")
    while process_command(*get_input()):
        pass


if __name__ == "__main__":
    main()
