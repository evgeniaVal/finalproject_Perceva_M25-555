from abc import ABC, abstractmethod

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig


class BaseApiClient(ABC):
    """Базовый абстрактный класс для API-клиентов получения курсов валют."""

    @abstractmethod
    def fetch_rates(self) -> dict:
        """Получает курсы валют из внешнего API.

        Raises:
            ApiRequestError: При ошибке запроса или парсинга.

        Returns:
            dict: Словарь с курсами в формате {"PAIR_KEY": rate}.
        """
        pass


class CoinGeckoClient(BaseApiClient):
    """Клиент для получения курсов криптовалют из CoinGecko API."""

    def __init__(self, config: ParserConfig):
        self.config = config

    def fetch_rates(self) -> dict:
        """Получает курсы криптовалют относительно USD из CoinGecko.

        Raises:
            ApiRequestError: При ошибке сетевого запроса или парсинга ответа.

        Returns:
            dict: Курсы в формате {"BTC_USD": 59337.21, ...}.
        """
        crypto_ids = ",".join(
            self.config.CRYPTO_ID_MAP[code] for code in self.config.CRYPTO_CURRENCIES
        )

        url = self.config.COINGECKO_URL
        params = {"ids": crypto_ids, "vs_currencies": self.config.BASE_CURRENCY.lower()}

        try:
            response = requests.get(
                url, params=params, timeout=self.config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 429:
                raise ApiRequestError(
                    "CoinGecko: Rate limit exceeded (429). Please try again later."
                )
            elif response.status_code == 401:
                raise ApiRequestError(
                    "CoinGecko: Unauthorized (401). Check your API key."
                )
            elif response.status_code == 403:
                raise ApiRequestError(
                    "CoinGecko: Access forbidden (403). API key may be invalid."
                )
            
            response.raise_for_status()
            data = response.json()

            result = {}
            base_lower = self.config.BASE_CURRENCY.lower()

            for code, crypto_id in self.config.CRYPTO_ID_MAP.items():
                if crypto_id in data and base_lower in data[crypto_id]:
                    pair_key = f"{code}_{self.config.BASE_CURRENCY}"
                    result[pair_key] = data[crypto_id][base_lower]

            return result

        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"CoinGecko request failed: {str(e)}")
        except (KeyError, ValueError) as e:
            raise ApiRequestError(f"CoinGecko response parsing failed: {str(e)}")


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для получения курсов фиатных валют из ExchangeRate-API."""

    def __init__(self, config: ParserConfig):
        self.config = config

    def fetch_rates(self) -> dict:
        """Получает курсы фиатных валют относительно USD.

        Raises:
            ApiRequestError: При отсутствии API-ключа или ошибке запроса.

        Returns:
            dict: Курсы в формате {"EUR_USD": 0.927, ...}.
        """
        if not self.config.EXCHANGERATE_API_KEY:
            raise ApiRequestError("EXCHANGERATE_API_KEY is not set")

        url = (
            f"{self.config.EXCHANGERATE_API_URL}/"
            f"{self.config.EXCHANGERATE_API_KEY}/"
            f"latest/{self.config.BASE_CURRENCY}"
        )

        try:
            response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
            
            if response.status_code == 429:
                raise ApiRequestError(
                    "ExchangeRate-API: Rate limit exceeded (429). "
                    "Please try again later."
                )
            elif response.status_code == 401:
                raise ApiRequestError(
                    "ExchangeRate-API: Unauthorized (401). Check your API key."
                )
            elif response.status_code == 403:
                raise ApiRequestError(
                    "ExchangeRate-API: Access forbidden (403). API key may be invalid."
                )
            
            response.raise_for_status()
            data = response.json()

            if data.get("result") != "success":
                error_type = data.get("error-type", "unknown")
                raise ApiRequestError(f"ExchangeRate-API returned error: {error_type}")

            rates = data.get("conversion_rates", {})
            result = {}

            for code in self.config.FIAT_CURRENCIES:
                if code in rates:
                    pair_key = f"{code}_{self.config.BASE_CURRENCY}"
                    result[pair_key] = rates[code]

            return result

        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"ExchangeRate-API request failed: {str(e)}")
        except (KeyError, ValueError) as e:
            raise ApiRequestError(f"ExchangeRate-API response parsing failed: {str(e)}")
