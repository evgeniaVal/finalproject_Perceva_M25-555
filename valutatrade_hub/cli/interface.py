from argparse import ArgumentParser
from datetime import datetime
from functools import wraps
from shlex import split as shlex_split

from prompt import string as prompt_string

from valutatrade_hub.core.currencies import get_supported_currencies
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.usecases import (
    buy,
    get_rate,
    login,
    register,
    sell,
    show_portfolio,
)
from valutatrade_hub.core.utils import load_json
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import ExchangeRatesStorage
from valutatrade_hub.parser_service.updater import RatesUpdater


def format_portfolio_result(data: dict) -> str:
    """Форматирует данные портфеля для вывода пользователю.

    Args:
        data (dict): Данные портфеля.

    Returns:
        str: Форматированная строка.
    """
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


def format_trade_result(data: dict, operation: str) -> str:
    """Форматирует результат торговой операции.

    Args:
        data (dict): Данные транзакции.
        operation (str): Тип операции ("Покупка" или "Продажа").

    Returns:
        str: Форматированная строка.
    """
    lines = []
    lines.append(
        f"{operation} выполнена: {data['amount']:.4f} {data['currency']} "
        f"по курсу {data['rate']:,.2f} {data['base_currency']}/{data['currency']}"
    )
    lines.append("Изменения в портфеле:")
    lines.append(
        f"- {data['currency']}: было {data['old_balance']:.4f} → "
        f"стало {data['new_balance']:.4f}"
    )
    cost_label = (
        "Оценочная стоимость покупки" if operation == "Покупка" else "Оценочная выручка"
    )
    lines.append(f"{cost_label}: {data['cost']:,.2f} {data['base_currency']}")
    return "\n".join(lines)


def format_rate_result(data: dict) -> str:
    """Форматирует информацию о курсе валюты.

    Args:
        data (dict): Данные курса.

    Returns:
        str: Форматированная строка.
    """
    from_cur = data["from_currency"]
    to_cur = data["to_currency"]
    rate = data["rate"]
    reverse_rate = data["reverse_rate"]
    updated_at = data.get("updated_at")

    lines = []

    if updated_at:
        dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"Курс {from_cur}→{to_cur}: {rate} (обновлено: {time_str})")
    else:
        lines.append(f"Курс {from_cur}→{to_cur}: {rate}")

    lines.append(f"Обратный курс {to_cur}→{from_cur}: {reverse_rate}")

    return "\n".join(lines)


def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except InsufficientFundsError as e:
            print(f"Ошибка: {e}")
        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e}")
            supported = get_supported_currencies()
            print(f"Поддерживаемые валюты: {', '.join(supported)}")
            print("Используйте 'get-rate --from <код> --to <код>' для получения курса")
        except ApiRequestError as e:
            print(f"Ошибка: {e}")
            print(
                "Пожалуйста, повторите попытку позже или проверьте сетевое соединение."
            )
        except Exception as e:
            print(e)
        return None

    return wrapper


buy = handle_errors(buy)
login = handle_errors(login)
register = handle_errors(register)
show_portfolio = handle_errors(show_portfolio)
sell = handle_errors(sell)
get_rate = handle_errors(get_rate)


def check_login(login_id):
    if login_id is None or login_id <= 0:
        print("Сначала выполните login.")
        return False
    return True


def handle_update_rates(source_filter: str | None = None):
    """Обрабатывает команду обновления курсов валют.

    Args:
        source_filter (str | None): Фильтр по источнику (coingecko/exchangerate).
    """
    try:
        config = ParserConfig()

        clients: list = []
        if source_filter is None:
            clients = [
                CoinGeckoClient(config),
                ExchangeRateApiClient(config),
            ]
        elif source_filter.lower() == "coingecko":
            clients = [CoinGeckoClient(config)]
        elif source_filter.lower() in ["exchangerate", "exchangerate-api"]:
            clients = [ExchangeRateApiClient(config)]
        else:
            print(f"Неизвестный источник: {source_filter}")
            print("Доступные источники: coingecko, exchangerate")
            return

        rates_path = config.RATES_FILE_PATH or "data/rates.json"
        history_path = config.HISTORY_FILE_PATH or "data/exchange_rates.json"

        storage = ExchangeRatesStorage(history_path, rates_path)
        updater = RatesUpdater(clients, storage)

        print("INFO: Starting rates update...")
        result = updater.run_update()

        if not result or result.get("total_rates", 0) == 0:
            print("ERROR: No rates fetched from any client")
            return

        total = result.get("total_rates", 0)
        timestamp = result.get("timestamp", "")
        successful = result.get("successful_sources", [])
        failed = result.get("failed_sources", [])

        print(f"Update successful. Total rates updated: {total}.")
        if timestamp:
            print(f"Last refresh: {timestamp}")

        if successful:
            print(f"Successful sources: {', '.join(successful)}")

        if failed:
            print(f"Failed sources: {', '.join(failed)}")

    except ApiRequestError as e:
        print(f"ERROR: {e}")
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")


def handle_show_rates(
    currency_filter: str | None = None,
    top: int | None = None,
    base_currency: str | None = None,
):
    """Отображает актуальные курсы из кэша.

    Args:
        currency_filter (str | None): Фильтр по валюте.
        top (int | None): Количество топовых курсов.
        base_currency (str | None): Базовая валюта.
    """
    try:
        config = ParserConfig()
        rates_path = config.RATES_FILE_PATH or "data/rates.json"
        data = load_json(rates_path, default=dict)

        last_refresh = data.get("last_refresh")
        pairs = data.get("pairs", {})

        if not pairs:
            print("Локальный кеш курсов пуст.")
            print("Выполните 'update-rates', чтобы загрузить данные.")
            return

        filtered_pairs = {}

        if currency_filter:
            currency_upper = currency_filter.upper()
            for pair_key, pair_data in pairs.items():
                from_cur = pair_key.split("_")[0]
                if from_cur == currency_upper:
                    filtered_pairs[pair_key] = pair_data

            if not filtered_pairs:
                print(f"Курс для '{currency_filter}' не найден в кеше.")
                return
        else:
            filtered_pairs = pairs

        if base_currency:
            base_upper = base_currency.upper()
            temp_pairs = {}
            for pair_key, pair_data in filtered_pairs.items():
                to_cur = pair_key.split("_")[1]
                if to_cur == base_upper:
                    temp_pairs[pair_key] = pair_data
            filtered_pairs = temp_pairs

        sorted_pairs = sorted(
            filtered_pairs.items(), key=lambda x: x[1]["rate"], reverse=True
        )

        if top and top > 0:
            sorted_pairs = sorted_pairs[:top]

        print(f"Rates from cache (updated at {last_refresh}):")
        for pair_key, pair_data in sorted_pairs:
            rate = pair_data["rate"]
            source = pair_data.get("source", "Unknown")
            print(f"- {pair_key}: {rate} (source: {source})")

    except Exception as e:
        print(f"ERROR: {e}")


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

    p_sell = sub.add_parser("sell", add_help=False)
    p_sell.add_argument("-c", "--currency", type=str, required=True)
    p_sell.add_argument("-a", "--amount", type=float, required=True)
    p_sell.set_defaults(command="sell")

    p_get_rate = sub.add_parser("get-rate", add_help=False)
    p_get_rate.add_argument("-f", "--from", dest="from_cur", type=str, required=True)
    p_get_rate.add_argument("-t", "--to", dest="to_cur", type=str, required=True)
    p_get_rate.set_defaults(command="get-rate")

    p_update_rates = sub.add_parser("update-rates", add_help=False)
    p_update_rates.add_argument("-s", "--source", type=str, required=False)
    p_update_rates.set_defaults(command="update-rates")

    p_show_rates = sub.add_parser("show-rates", add_help=False)
    p_show_rates.add_argument("-c", "--currency", type=str, required=False)
    p_show_rates.add_argument("-t", "--top", type=int, required=False)
    p_show_rates.add_argument("-b", "--base", type=str, required=False)
    p_show_rates.set_defaults(command="show-rates")

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
            result = register(ns.username, ns.password)
            if result:
                idx = result["user_id"]
                print(
                    f"Пользователь '{ns.username}' успешно зарегистрирован (id={idx})."
                    f" Войдите: login --username {ns.username} --password ****"
                )
            return logged_id, True
        case "login":
            result = login(ns.username, ns.password)
            if result:
                new_id = result["user_id"]
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
                print(format_trade_result(result, "Покупка"))
            return logged_id, True
        case "sell":
            if not check_login(logged_id):
                return logged_id, True
            result = sell(logged_id, ns.currency, ns.amount)
            if result:
                print(format_trade_result(result, "Продажа"))
            return logged_id, True
        case "get-rate":
            result = get_rate(ns.from_cur, ns.to_cur)
            if result:
                print(format_rate_result(result))
            return logged_id, True
        case "update-rates":
            handle_update_rates(ns.source)
            return logged_id, True
        case "show-rates":
            handle_show_rates(ns.currency, ns.top, ns.base)
            return logged_id, True
        case _:
            return logged_id, True


def main():
    """Главная функция - точка входа в приложение."""
    parser = build_parser()
    print("Приветствие!")
    not_over = True
    logged_id = None
    while not_over:
        logged_id, not_over = process_command(logged_id, parser, get_input())


if __name__ == "__main__":
    main()
