"""
HolidayService — Async client for the Public Holiday API.

Uses the free Nager.Date API (https://date.nager.at) by default.
No API key is required for Nager.Date; an optional key field is present
in Settings for teams that prefer a paid provider.

Responsibilities:
  - Fetch public holidays for a country and year
  - Determine whether a given date is a working day
  - Count working days in a date range (for deadline analysis)
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Set

import httpx

from app.core.config import settings


class HolidayServiceError(Exception):
    """Raised when the Holiday API returns an unexpected response."""


class HolidayData:
    """Lightweight value object for a single public holiday."""

    __slots__ = ("date", "local_name", "name", "country_code", "is_global")

    def __init__(
        self,
        holiday_date: date,
        local_name: str,
        name: str,
        country_code: str,
        is_global: bool = True,
    ) -> None:
        self.date = holiday_date
        self.local_name = local_name
        self.name = name
        self.country_code = country_code
        self.is_global = is_global

    def __repr__(self) -> str:
        return f"<HolidayData {self.date} '{self.name}' ({self.country_code})>"


class HolidayService:
    """
    Async wrapper around the Nager.Date Public Holiday API.

    Designed for use as an async context manager::

        async with HolidayService() as svc:
            holidays = await svc.get_holidays("TR", 2025)
            working = svc.is_working_day(date(2025, 1, 6), holidays)
    """

    _HOLIDAYS_PATH = "/PublicHolidays/{year}/{country_code}"

    def __init__(self) -> None:
        self._base_url = str(settings.HOLIDAY_API_BASE_URL).rstrip("/")
        base_headers: Dict[str, str] = {"Accept": "application/json"}
        if settings.HOLIDAY_API_KEY:
            base_headers["X-Api-Key"] = settings.HOLIDAY_API_KEY
        self._headers = base_headers
        self._client: Optional[httpx.AsyncClient] = None

        # Simple in-process cache: (country, year) → list of holiday dates
        self._cache: Dict[tuple[str, int], Set[date]] = {}

    # ── Context manager ────────────────────────────────────────────────────────
    async def __aenter__(self) -> "HolidayService":
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=self._headers,
            timeout=httpx.Timeout(15.0),
        )
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    # ── Public API ─────────────────────────────────────────────────────────────
    async def get_holidays(
        self,
        country_code: str,
        year: int,
    ) -> List[HolidayData]:
        """
        Fetch all public holidays for a given country and year.

        Args:
            country_code: ISO 3166-1 alpha-2 code (e.g. "TR", "US", "DE").
            year:         Calendar year (e.g. 2025).

        Returns:
            List of :class:`HolidayData` sorted by date ascending.

        Raises:
            HolidayServiceError: On HTTP errors or unsupported country codes.
        """
        self._ensure_client()
        code = country_code.upper()

        response = await self._client.get(  # type: ignore[union-attr]
            self._HOLIDAYS_PATH.format(year=year, country_code=code)
        )
        self._raise_for_status(response, code, year)

        raw: List[Dict[str, Any]] = response.json()
        holidays = [self._map_holiday(item, code) for item in raw]
        holidays.sort(key=lambda h: h.date)

        # Populate cache for is_working_day calls
        self._cache[(code, year)] = {h.date for h in holidays}

        return holidays

    async def get_holiday_dates(
        self,
        country_code: str,
        year: int,
    ) -> Set[date]:
        """
        Return a set of holiday dates for fast O(1) lookup.

        Uses the internal cache so repeated calls within the same service
        instance won't make duplicate HTTP requests.
        """
        code = country_code.upper()
        cache_key = (code, year)
        if cache_key not in self._cache:
            await self.get_holidays(code, year)
        return self._cache[cache_key]

    @staticmethod
    def is_working_day(
        target_date: date,
        holiday_dates: Set[date],
    ) -> bool:
        """
        Return True if *target_date* is a working day.

        A working day is any day that is:
          - NOT a Saturday (weekday == 5)
          - NOT a Sunday  (weekday == 6)
          - NOT in *holiday_dates*

        Args:
            target_date:   The date to check.
            holiday_dates: Set of public holiday dates (from get_holiday_dates).
        """
        return target_date.weekday() < 5 and target_date not in holiday_dates

    async def count_working_days(
        self,
        start: date,
        end: date,
        country_code: str,
    ) -> int:
        """
        Count the number of working days between *start* and *end* (inclusive).

        Fetches holidays for each calendar year that overlaps the range,
        so multi-year ranges work correctly.

        Args:
            start:        Range start date (inclusive).
            end:          Range end date (inclusive).
            country_code: ISO 3166-1 alpha-2 code for holiday lookups.

        Returns:
            Number of working days as an integer.
        """
        # Collect holidays for every year that the range spans
        all_holiday_dates: Set[date] = set()
        for year in range(start.year, end.year + 1):
            year_holidays = await self.get_holiday_dates(country_code, year)
            all_holiday_dates |= year_holidays

        working_days = 0
        current = start
        while current <= end:
            if self.is_working_day(current, all_holiday_dates):
                working_days += 1
            current += timedelta(days=1)

        return working_days

    # ── Private helpers ────────────────────────────────────────────────────────
    def _ensure_client(self) -> None:
        if self._client is None:
            raise RuntimeError(
                "HolidayService must be used as an async context manager. "
                "Use `async with HolidayService() as svc:`"
            )

    @staticmethod
    def _raise_for_status(
        response: httpx.Response,
        country_code: str,
        year: int,
    ) -> None:
        if response.status_code == 404:
            raise HolidayServiceError(
                f"No holiday data found for country '{country_code}' in {year}. "
                "Verify the ISO 3166-1 alpha-2 country code."
            )
        if response.is_error:
            raise HolidayServiceError(
                f"Holiday API error {response.status_code}: {response.text}"
            )

    @staticmethod
    def _map_holiday(raw: Dict[str, Any], country_code: str) -> HolidayData:
        """Map a raw Nager.Date JSON object to a :class:`HolidayData`."""
        raw_date = raw.get("date", "")
        parsed_date = date.fromisoformat(raw_date) if raw_date else date.today()
        return HolidayData(
            holiday_date=parsed_date,
            local_name=raw.get("localName", ""),
            name=raw.get("name", ""),
            country_code=country_code,
            is_global=raw.get("global", True),
        )
