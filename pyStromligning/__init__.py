"""Define pyStromligning library."""

from __future__ import annotations

import logging
import sys
import threading

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

    def __init__(self, lat: float, lon: float) -> None:
        """Initialize the :class:Stromligning class and set default attribute values."""
        _LOGGER.debug("Initializing the pyStromligning library")

        self._location: dict = {"lat": lat, "lon": lon}
        self._supplier: dict = {}
        self._company_id: str = None

        self._supplier = self._get_supplier()

        self.prices: dict = {}

    def set_company(self, company_id: str) -> None:
        """Set the selected company."""
        self._company_id = company_id

    def _get_supplier(self) -> dict:
        """Get the supplier for the provided location."""
        return self._get_response(
            f"/suppliers/find?lat={self._location['lat']}&long={self._location['lon']}"
        )

    def get_companies(self) -> dict:
        """Get a list of available electricity companies for the location."""
        companies = self._get_response(
            f"/companies?region={self._supplier[0]['priceArea']}"
        )
        company_list: dict = {}
        for company in companies:
            for product in company["products"]:
                company_list.update({"id": product["id"], "name": product["name"]})

        return company_list

    def update(self) -> dict:
        """Get current available prices."""
        return self._get_response(
            f"/prices?productId={self._company_id}&supplierId={self._supplier[0]['id']}"
        )

    def _get_response(self, path: str) -> dict:
        """Make the request to the API."""

        response = requests.request(
            "GET",
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
