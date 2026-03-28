"""
Market / transfer candidate pool.

TODO: REPLACE_WITH_REAL_MARKET_PROVIDER — live prices and availability from FPL transfers
endpoint (requires user auth in real product). For hackathon, bootstrap elements minus squad
is used inside transfer_service.
"""

from abc import ABC, abstractmethod
from typing import Any


class MarketDataProvider(ABC):
    @abstractmethod
    async def get_candidates(self, exclude_ids: set[int]) -> list[dict[str, Any]]:
        """Return player dicts compatible with internal Player building."""
