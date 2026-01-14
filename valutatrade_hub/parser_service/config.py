import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_env_file():
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        return

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")

            if key and key not in os.environ:
                os.environ[key] = value


_load_env_file()


@dataclass
class ParserConfig:
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "")

    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    BASE_CURRENCY: str = "USD"
    FIAT_CURRENCIES: tuple = ("EUR", "GBP", "RUB")
    CRYPTO_CURRENCIES: tuple = ("BTC", "ETH", "SOL")
    CRYPTO_ID_MAP: dict[str, str] = field(
        default_factory=lambda: {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
        }
    )

    RATES_FILE_PATH: str | None = None
    HISTORY_FILE_PATH: str | None = None

    REQUEST_TIMEOUT: int = 10

    def __post_init__(self):
        if self.RATES_FILE_PATH is None:
            project_root = Path(__file__).parent.parent.parent
            self.RATES_FILE_PATH = str(project_root / "data" / "rates.json")

        if self.HISTORY_FILE_PATH is None:
            project_root = Path(__file__).parent.parent.parent
            self.HISTORY_FILE_PATH = str(project_root / "data" / "exchange_rates.json")
