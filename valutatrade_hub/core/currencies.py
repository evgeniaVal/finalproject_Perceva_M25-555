from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    _name: str
    _code: str

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Currency name cannot be empty.")
        self._name = name.strip()

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, code: str):
        if (
            not isinstance(code, str)
            or not code.strip()
            or not 2 <= len(code.strip()) <= 5
            or not code.strip().isupper()
        ):
            raise ValueError("Currency code must be 2-5 uppercase letters.")
        self._code = code.strip().upper()

    def __init__(self, name: str, code: str):
        self.name = name
        self.code = code

    @abstractmethod
    def get_display_info(self) -> str:
        return f"{self.name} ({self.code})"


class FiatCurrency(Currency):
    _issuing_country: str

    @property
    def issuing_country(self):
        return self._issuing_country

    @issuing_country.setter
    def issuing_country(self, country: str):
        if not isinstance(country, str) or not country.strip():
            raise ValueError("Issuing country cannot be empty.")
        self._issuing_country = country.strip()

    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} - {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    _algorithm: str
    _market_cap: float

    @property
    def algorithm(self):
        return self._algorithm

    @algorithm.setter
    def algorithm(self, algorithm: str):
        if not isinstance(algorithm, str) or not algorithm.strip():
            raise ValueError("Algorithm cannot be empty.")
        self._algorithm = algorithm.strip()

    @property
    def market_cap(self):
        return self._market_cap

    @market_cap.setter
    def market_cap(self, market_cap: float):
        if not isinstance(market_cap, (int, float)) or market_cap < 0:
            raise ValueError("Market cap must be a non-negative number.")
        self._market_cap = float(market_cap)

    def __init__(self, name: str, code: str, algorithm: str, market_cap: float):
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} - {self.name}"
            f" (Algo: {self.algorithm}, MCAP: {self.market_cap})"
        )


_CURRENCY_REGISTRY: dict[str, Currency] = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.0e10),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 1.0e5),
}


def get_currency(code: str) -> Currency:
    if not isinstance(code, str) or not code.strip():
        raise CurrencyNotFoundError(code if code else "")
    normalized_code = code.strip().upper()
    currency = _CURRENCY_REGISTRY.get(normalized_code)
    if currency is None:
        raise CurrencyNotFoundError(normalized_code)
    return currency


def get_supported_currencies() -> list[str]:
    return sorted(_CURRENCY_REGISTRY.keys())
