class CurrencyNotFoundError(Exception):
    def __init__(self, code):
        self.code = str(code).strip()
        super().__init__(f"Неизвестная валюта '{self.code}'")
