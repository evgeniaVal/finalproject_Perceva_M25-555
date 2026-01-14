from datetime import datetime, timezone
from pathlib import Path

from valutatrade_hub.core.utils import load_json, save_json
from valutatrade_hub.logging_config import get_logger


class ExchangeRatesStorage:
    """Хранилище для курсов валют: история и кэш."""

    def __init__(self, history_file_path: str, rates_file_path: str):
        self.history_file_path = Path(history_file_path)
        self.rates_file_path = Path(rates_file_path)
        self.logger = get_logger()

    def save_rates(
        self, rates: dict[str, float], source: str, timestamp: str | None = None
    ) -> None:
        """Сохраняет курсы в историю и обновляет кэш.

        Args:
            rates (dict[str, float]): Курсы в формате {"PAIR": rate}.
            source (str): Источник данных.
            timestamp (str | None): Время обновления (ISO формат).
        """
        if timestamp is None:
            ts = datetime.now(timezone.utc).isoformat()
            timestamp = ts.replace("+00:00", "Z")

        self._append_to_history(rates, source, timestamp)
        self._update_cache(rates, source, timestamp)

    def _append_to_history(
        self, rates: dict[str, float], source: str, timestamp: str
    ) -> None:
        history = load_json(self.history_file_path, default=list)

        added_count = 0
        for pair_key, rate in rates.items():
            if "_" not in pair_key:
                self.logger.warning(f"Invalid pair key format: {pair_key}")
                continue

            from_currency, to_currency = pair_key.split("_", 1)

            record_id = f"{from_currency}_{to_currency}_{timestamp}"

            if any(record.get("id") == record_id for record in history):
                continue

            record = {
                "id": record_id,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "rate": rate,
                "timestamp": timestamp,
                "source": source,
                "meta": {},
            }
            history.append(record)
            added_count += 1

        save_json(self.history_file_path, history)
        self.logger.info(f"Appended {added_count} rates to history")

    def _update_cache(
        self, rates: dict[str, float], source: str, timestamp: str
    ) -> None:
        cache = load_json(self.rates_file_path, default=dict)

        pairs = cache.get("pairs", {})
        updated_count = 0

        for pair_key, rate in rates.items():
            current_entry = pairs.get(pair_key, {})
            current_updated_at = current_entry.get("updated_at", "")

            if timestamp >= current_updated_at:
                pairs[pair_key] = {
                    "rate": rate,
                    "updated_at": timestamp,
                    "source": source,
                }
                updated_count += 1

        cache["pairs"] = pairs
        cache["last_refresh"] = timestamp

        save_json(self.rates_file_path, cache)
        self.logger.info(f"Updated cache with {updated_count} rates")

    def get_cached_rates(self) -> dict:
        """Возвращает актуальные курсы из кэша.

        Returns:
            dict: Словарь с курсами.
        """
        cache = load_json(self.rates_file_path, default=dict)
        return cache.get("pairs", {})

    def get_history(
        self,
        from_currency: str | None = None,
        to_currency: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Возвращает историю курсов с фильтрацией.

        Args:
            from_currency (str | None): Фильтр по исходной валюте.
            to_currency (str | None): Фильтр по целевой валюте.
            limit (int | None): Максимальное количество записей.

        Returns:
            list[dict]: Список записей истории (отсортированных по времени).
        """
        history = load_json(self.history_file_path, default=list)

        filtered = history

        if from_currency:
            filtered = [r for r in filtered if r.get("from_currency") == from_currency]

        if to_currency:
            filtered = [r for r in filtered if r.get("to_currency") == to_currency]

        filtered = sorted(filtered, key=lambda x: x.get("timestamp", ""), reverse=True)

        if limit:
            filtered = filtered[:limit]

        return filtered
