class CurrencyNotFoundError(Exception):
    def __init__(self, code):
        self.code = str(code).strip()
        super().__init__(f"Неизвестная валюта '{self.code}'")


class InsufficientFundsError(Exception):
    def __init__(self, available: float, required: float, currency_code: str):
        self.available = available
        self.required = required
        self.currency_code = currency_code
        super().__init__(
            f"Недостаточно средств: доступно {available} {currency_code}, "
            f"требуется {required} {currency_code}"
        )


class ApiRequestError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")
