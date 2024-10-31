"""Define pyStromligning library."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from operator import itemgetter

import requests

from .const import API_URL
from .exceptions import InvalidAPIResponse, TooManyRequests

if sys.version_info < (3, 11, 0):
    sys.exit("The pyWorxcloud module requires Python 3.11.0 or later")

_LOGGER = logging.getLogger(__name__)


class Stromligning:
    """
    Stromligning library

    Used for handling the communication with the Stromligning API.

    Results are electricity prices that takes into account the tariffs and other fees.
    """

    def __init__(self) -> None:
        """Initialize the :class:Stromligning class and set default attribute values."""
        _LOGGER.debug("Initializing the pyStromligning library")
        self._location: dict = {}

        self.supplier: dict = {}
        self.available_companies: list = []

        self.prices: dict = {}
        self.company: dict = {}

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
                    {"id": product["id"], "name": f"{company_name} - {product['name']}"}
                )

        return sorted(company_list, key=itemgetter("name"))

    def update(self, start:str=None) -> None:
        """Get current available prices."""
        if start is None:
            start = (
                datetime.now()
                .replace(hour=0, minute=0, second=0, microsecond=0)
                .astimezone(timezone.utc)
                .isoformat()
            ).replace("+00:00", ".000Z")

        url = f"/prices?productId={self.company['id']}&supplierId={self.supplier['id']}&from={start}"

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

    def _get_response(self, path: str) -> dict:
        """Make the request to the API."""

        response = requests.get(
            f"{API_URL}{path}",
            timeout=60,
        )

        if response.status_code != 200:
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
