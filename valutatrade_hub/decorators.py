import functools
import inspect
from typing import Any, Callable

from valutatrade_hub.logging_config import get_logger


def log_action(
    action_name: str | None = None, verbose: bool = False
) -> Callable[[Callable], Callable]:
    def decorator(func: Callable) -> Callable:
        action = (
            action_name.upper()
            if action_name
            else func.__name__.upper().replace("_", "-")
        )

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = get_logger()

            params = _extract_params(func, args, kwargs)
            error = None
            result = None

            try:
                result = func(*args, **kwargs)
                if isinstance(result, dict):
                    _update_params_from_result(params, result)
                _log_operation(logger, action, params, verbose, True, None)
                return result
            except Exception as e:
                error = e
                _log_operation(logger, action, params, verbose, False, error)
                raise

        return wrapper

    return decorator


def _extract_params(func: Callable, args: tuple, kwargs: dict) -> dict:
    sig = inspect.signature(func)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()

    params = {}
    arguments = bound.arguments

    param_mapping = {
        "username": "username",
        "user_id": "user_id",
        "currency": "currency_code",
        "currency_code": "currency_code",
        "amount": "amount",
    }

    for arg_key, param_key in param_mapping.items():
        if arg_key in arguments:
            params[param_key] = arguments[arg_key]

    return params


def _update_params_from_result(params: dict, result_data: dict) -> None:
    result_mapping = {
        "username": "username",
        "currency": "currency_code",
        "rate": "rate",
        "base_currency": "base",
        "old_balance": "old_balance",
        "new_balance": "new_balance",
    }

    for result_key, param_key in result_mapping.items():
        if result_key in result_data:
            params[param_key] = result_data[result_key]

    if "username" in params:
        params.pop("user_id", None)


def _build_log_message(
    action: str,
    params: dict,
    verbose: bool,
    success: bool,
    error: Exception | None = None,
) -> str:
    log_parts = [action]

    if "username" in params:
        log_parts.append(f"user='{params['username']}'")
    elif "user_id" in params:
        log_parts.append(f"user_id={params['user_id']}")

    if "currency_code" in params:
        log_parts.append(f"currency='{params['currency_code']}'")

    if "amount" in params:
        log_parts.append(f"amount={params['amount']:.4f}")

    if "rate" in params:
        log_parts.append(f"rate={params['rate']:.2f}")

    if "base" in params:
        log_parts.append(f"base='{params['base']}'")

    if verbose and "old_balance" in params and "new_balance" in params:
        log_parts.append(
            f"balance_change={params['old_balance']:.4f}->{params['new_balance']:.4f}"
        )

    log_parts.append("result=OK" if success else "result=ERROR")

    if error:
        log_parts.append(f"error_type={type(error).__name__}")
        log_parts.append(f"error_message='{error}'")

    return " ".join(log_parts)


def _log_operation(
    logger,
    action: str,
    params: dict,
    verbose: bool,
    success: bool,
    error: Exception | None,
) -> None:
    message = _build_log_message(action, params, verbose, success, error)
    logger.info(message)
