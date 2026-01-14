from datetime import datetime, timezone
from typing import Sequence

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.logging_config import get_logger
from valutatrade_hub.parser_service.api_clients import BaseApiClient
from valutatrade_hub.parser_service.storage import ExchangeRatesStorage


class RatesUpdater:
    """Координатор обновления курсов валют из различных источников."""

    def __init__(self, clients: Sequence[BaseApiClient], storage: ExchangeRatesStorage):
        self.clients = clients
        self.storage = storage
        self.logger = get_logger()

    def run_update(self) -> dict:
        """Запускает процесс обновления курсов из всех клиентов.

        Returns:
            dict: Результат обновления (total_rates, successful_sources,
                failed_sources, timestamp).
        """
        self.logger.info("Starting rates update...")

        all_rates = {}
        successful_sources = []
        failed_sources = []

        for client in self.clients:
            client_name = client.__class__.__name__
            try:
                self.logger.info(f"Fetching from {client_name}...")
                rates = client.fetch_rates()
                all_rates.update(rates)
                successful_sources.append(client_name)
                self.logger.info(
                    f"{client_name} fetched successfully ({len(rates)} rates)"
                )
            except ApiRequestError as e:
                failed_sources.append(client_name)
                self.logger.error(f"{client_name} failed: {e.reason}")
            except Exception as e:
                failed_sources.append(client_name)
                self.logger.error(f"{client_name} failed: {str(e)}")

        if not all_rates:
            self.logger.warning("No rates fetched from any source")
            ts = datetime.now(timezone.utc).isoformat()
            return {
                "total_rates": 0,
                "successful_sources": successful_sources,
                "failed_sources": failed_sources,
                "timestamp": ts.replace("+00:00", "Z"),
            }

        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        self.storage.save_rates(all_rates, source="ParserService", timestamp=timestamp)

        self.logger.info(
            f"Update completed: {len(all_rates)} rates from "
            f"{len(successful_sources)} sources"
        )

        return {
            "total_rates": len(all_rates),
            "successful_sources": successful_sources,
            "failed_sources": failed_sources,
            "timestamp": timestamp,
        }
