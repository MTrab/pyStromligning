"""Define pyStromligning library."""

from __future__ import annotations

import logging
import math
import sys
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from operator import itemgetter

import requests

from .const import API_URL, DEV_API_URL
from .exceptions import (
    FixedPriceRequired,
    InvalidAPIKey,
    InvalidAPIResponse,
    TooManyRequests,
)

if sys.version_info < (3, 11, 0):
    sys.exit("The pyWorxcloud module requires Python 3.11.0 or later")

_LOGGER = logging.getLogger(__name__)

try:
    LIBRARY_USER_AGENT = f"pystromligning/{version('pystromligning')}"
except PackageNotFoundError:
    LIBRARY_USER_AGENT = "pystromligning"


def _midnight_utc() -> str:
    """Return local midnight today as a UTC timestamp for the API."""
    return (
        datetime.now()
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .astimezone(timezone.utc)
        .isoformat()
    ).replace("+00:00", ".000Z")


class Aggregation(str):
    """Strømligning aggregation levels."""

    MIN15 = "15m"
    HOUR = "1h"

    @classmethod
    def values(cls):
        """Return a list of all aggregation levels dynamically."""
        return [
            value
            for key, value in vars(cls).items()
            if not key.startswith("__") and isinstance(value, str)
        ]


class Stromligning:
    """
    Stromligning library

    Used for handling the communication with the Stromligning API.

    Results are electricity prices that takes into account the tariffs and other fees.
    """

    def __init__(
        self,
        dev: bool = False,
        api_key: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Initialize the :class:Stromligning class and set default attribute values.

        ``user_agent`` identifies the calling application, for example
        ``"MyApp/1.0"``; the library's own name and version are appended.
        ``api_key`` is sent as a bearer token when set.
        """
        _LOGGER.debug("Initializing the pyStromligning library")
        self._location: dict = {}

        self.supplier: dict = {}
        self.available_companies: list = []

        self.prices: list = []
        self.production_prices: list = []
        self.company: dict = {}
        self.aggregation: str = Aggregation.HOUR
        self.forecast: bool = False
        self.electricity_price: float | None = None

        self.dev_api: bool = dev
        self._api_key: str | None = None
        self.set_api_key(api_key)
        self.user_agent: str = (
            f"{user_agent} {LIBRARY_USER_AGENT}" if user_agent else LIBRARY_USER_AGENT
        )

    def set_api_key(self, api_key: str | None) -> None:
        """Set or clear the API key. Empty or blank keys are treated as no key."""
        if api_key is not None and not isinstance(api_key, str):
            raise TypeError("API key must be a string")
        self._api_key = api_key.strip() if api_key and api_key.strip() else None

    def _headers(self) -> dict:
        """Return request headers; the API key is never logged."""
        headers = {"User-Agent": self.user_agent}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def set_forecast(self, forecast: bool) -> None:
        """Set if forecast prices should be used."""
        self.forecast = forecast

    def set_electricity_price(self, price: float | None) -> None:
        """Set the agreed electricity price in kr/kWh excluding VAT."""
        if price is not None:
            if isinstance(price, bool) or not isinstance(price, (int, float)):
                raise TypeError("Electricity price must be numeric")
            if not math.isfinite(price) or price < 0:
                raise ValueError("Electricity price must be finite and non-negative")
        self.electricity_price = price

    def set_aggregation(self, aggregation: Aggregation) -> None:
        """Set aggregation level."""
        self.aggregation = aggregation

    def set_location(self, lat: float, lon: float) -> None:
        """Set location."""
        self._location: dict = {"lat": lat, "lon": lon}

        self.supplier = self._get_supplier()
        self.available_companies = self._get_companies()

    def set_company(self, company_id: str) -> None:
        """Set the selected company."""
        for company in self.available_companies:
            if company["id"] == company_id:
                self.company = company
                break
            else:
                self.company = {}

    def _get_supplier(self) -> dict:
        """Get the supplier for the provided location."""
        return (
            self._get_response(
                f"/suppliers/find?lat={self._location['lat']}&long={self._location['lon']}"
            )
        )[0]

    def _get_companies(self) -> list:
        """Get a list of available electricity companies for the location."""
        companies = self._get_response(
            f"/companies?region={self.supplier['priceArea']}"
        )
        company_list: list = []
        for company in companies:
            company_name = company["name"]
            for product in company["products"]:
                company_list.append(
                    {
                        "id": product["id"],
                        "name": f"{company_name} - {product['name']}",
                        "productType": product["productType"],
                    }
                )

        return sorted(company_list, key=itemgetter("name"))

    def update(self, start: str | None = None) -> None:
        """Get current available prices."""
        if start is None:
            start = _midnight_utc()

        aggregation = ""
        if self.aggregation != Aggregation.MIN15:
            aggregation = "&aggregation=" + self.aggregation

        url = (
            f"/prices?productId={self.company['id']}"
            f"&supplierId={self.supplier['id']}&from={start}{aggregation}"
            f"&forecast={str(self.forecast).lower()}"
        )

        if self.company["productType"] == "fixed":
            if self.electricity_price is None:
                raise FixedPriceRequired(
                    "Set the agreed electricity price before updating"
                )
            url += f"&electricityPrice={self.electricity_price}"

        _LOGGER.debug("Fetching electricity prices")

        price_list: list = []
        price_list_raw = sorted(
            (self._get_response(url))["prices"],
            key=itemgetter("date"),
        )

        for price in price_list_raw:
            if price in price_list:
                continue

            price_list.append(price)

        self.prices = price_list

    def update_production(self, start: str | None = None) -> None:
        """Get sale prices for surplus production at the selected grid supplier.

        Prices are spot prices excluding VAT, less the production tariffs from
        Energinet and the grid supplier. Tariff deductions are negative values.
        """
        if start is None:
            start = _midnight_utc()

        aggregation = ""
        if self.aggregation != Aggregation.MIN15:
            aggregation = "&aggregation=" + self.aggregation

        url = (
            f"/prices/production?supplierId={self.supplier['id']}"
            f"&from={start}{aggregation}"
            f"&forecast={str(self.forecast).lower()}"
        )

        _LOGGER.debug("Fetching production prices")

        price_list: list = []
        for price in sorted(
            (self._get_response(url))["prices"],
            key=itemgetter("date"),
        ):
            if price not in price_list:
                price_list.append(price)

        self.production_prices = price_list

    def _get_response(self, path: str) -> dict:
        """Make the request to the API."""

        response = requests.get(
            f"{DEV_API_URL if self.dev_api else API_URL}{path}",
            headers=self._headers(),
            timeout=60,
        )

        if response.status_code != 200:
            if response.status_code == 401:
                raise InvalidAPIKey(
                    "The API key was rejected (invalid, deactivated or expired)"
                )
            if response.status_code == 429:
                raise TooManyRequests(
                    "Too many requests from this IP, please try again after 15 minutes"
                )
            else:
                raise InvalidAPIResponse(
                    f"Error {response.status_code} received from the API"
                )
        else:
            return response.json()
