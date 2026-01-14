import time
from datetime import datetime

from valutatrade_hub.logging_config import get_logger


class RatesScheduler:
    def __init__(self, update_callback, interval_seconds: int = 3600):
        self.update_callback = update_callback
        self.interval_seconds = interval_seconds
        self.logger = get_logger()
        self._is_running = False

    def run(self) -> None:
        self._is_running = True
        self.logger.info(f"Scheduler started with interval {self.interval_seconds}s")

        while self._is_running:
            try:
                self.logger.info(
                    f"Scheduled update started at {datetime.now().isoformat()}"
                )
                self.update_callback()
                self.logger.info("Scheduled update completed successfully")

            except Exception as e:
                self.logger.error(f"Scheduled update failed: {str(e)}")

            if not self._is_running:
                break

            time.sleep(self.interval_seconds)

        self.logger.info("Scheduler stopped")

    def stop(self) -> None:
        self._is_running = False

    def is_running(self) -> bool:
        return self._is_running

    def set_interval(self, interval_seconds: int) -> None:
        if interval_seconds < 60:
            self.logger.warning(
                f"Interval {interval_seconds}s is too short, minimum is 60s"
            )
            interval_seconds = 60

        self.interval_seconds = interval_seconds
        self.logger.info(f"Scheduler interval updated to {interval_seconds}s")
