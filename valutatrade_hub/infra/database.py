from pathlib import Path

from valutatrade_hub.core.utils import load_json, save_json
from valutatrade_hub.infra.settings import SettingsLoader


class DatabaseManager:
    """
    Singleton для управления доступом к данным (JSON-хранилище).
    Реализован через __new__ для простоты и читабельности:
    - Не требует метакласса
    - Явный контроль создания экземпляра в одном месте
    - Понятен, так как рассматривался в курсах
    """
    _instance: "DatabaseManager | None" = None
    _initialized: bool = False

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._settings = SettingsLoader()
        self._initialized = True

    def _get_file_path(self, filename: str) -> Path:
        data_dir = Path(self._settings.get("data_dir", "data"))
        return data_dir / filename

    def load_users(self) -> list[dict]:
        filename = self._settings.get("users_file", "users.json")
        path = self._get_file_path(filename)
        return load_json(path, default=list)

    def save_users(self, users: list[dict]) -> None:
        filename = self._settings.get("users_file", "users.json")
        path = self._get_file_path(filename)
        save_json(path, users)

    def load_portfolios(self) -> list[dict]:
        filename = self._settings.get("portfolios_file", "portfolios.json")
        path = self._get_file_path(filename)
        return load_json(path, default=list)

    def save_portfolios(self, portfolios: list[dict]) -> None:
        filename = self._settings.get("portfolios_file", "portfolios.json")
        path = self._get_file_path(filename)
        save_json(path, portfolios)

    def load_rates(self) -> dict:
        filename = self._settings.get("rates_file", "rates.json")
        path = self._get_file_path(filename)
        return load_json(path, default=dict)

    def save_rates(self, rates: dict) -> None:
        filename = self._settings.get("rates_file", "rates.json")
        path = self._get_file_path(filename)
        save_json(path, rates)
