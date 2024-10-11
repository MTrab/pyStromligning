"""Define pyStromligning library."""

from __future__ import annotations

import logging
import sys

if sys.version_info < (3, 11, 0):
    sys.exit("The pyWorxcloud module requires Python 3.9.0 or later")

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
        self._supplier: dict = {}
        self._company_id: str = None

    def set_location(self, lat: float, lon: float) -> None:
        """Set the location for fetching tariffs."""
        self._location.update({"lat": lat, "lon": lon})
        self._supplier = self._get_supplier()

    def set_company(self, company_id: str) -> None:
        """Set the selected company."""
        self._company_id = company_id

    def _get_supplier(self) -> dict:
        """Get the supplier for the provided location."""
        supplier: dict = {}

        return supplier

    def get_companies(self) -> dict:
        """Get a list of available electricity companies for the location."""

    def get_available_prices(self) -> dict:
        """Get current available prices."""
