from __future__ import annotations

import time
from abc import ABC, abstractmethod

from src.config import Settings
from src.models.job import JobListing


class JobSource(ABC):
    name = "base"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @abstractmethod
    def fetch(self, keywords: list[str], locations: list[str]) -> list[JobListing]:
        raise NotImplementedError

    def polite_pause(self) -> None:
        if self.settings.rate_limit_seconds > 0:
            time.sleep(self.settings.rate_limit_seconds)
