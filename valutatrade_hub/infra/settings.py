import tomllib
from pathlib import Path
from typing import Any


class SettingsLoader:
    """
    Singleton для управления конфигурацией приложения.
    Реализован через __new__ для простоты и читабельности:
    - Не требует метакласса
    - Явный контроль создания экземпляра в одном месте
    - Понятен, так как рассматривался в курсах
    """
    _instance: "SettingsLoader | None" = None
    _initialized: bool = False

    def __new__(cls) -> "SettingsLoader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._config: dict[str, Any] = {}
        self._load_config()
        self._initialized = True

    def _load_config(self) -> None:
        project_root = Path(__file__).parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"

        defaults = {
            "data_dir": str(project_root / "data"),
            "logs_dir": str(project_root / "logs"),
            "rates_ttl_seconds": 3600,
            "default_base_currency": "USD",
            "users_file": "users.json",
            "portfolios_file": "portfolios.json",
            "rates_file": "rates.json",
            "log_format": "human",
        }

        if pyproject_path.exists():
            try:
                with open(pyproject_path, "rb") as f:
                    pyproject_data = tomllib.load(f)
                    tool_config = pyproject_data.get("tool", {}).get("valutatrade", {})
                    defaults.update(tool_config)
            except Exception:
                pass

        self._config = defaults

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def reload(self) -> None:
        self._config = {}
        self._load_config()

    @property
    def rates_ttl(self) -> int:
        return int(self.get("rates_ttl_seconds", 3600))

    @property
    def base_currency(self) -> str:
        return str(self.get("default_base_currency", "USD"))

    def __repr__(self) -> str:
        return f"<SettingsLoader(config_keys={list(self._config.keys())})>"
