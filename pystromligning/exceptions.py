"""Custom exceptions used in the pyStromligning library."""


class InvalidAPIResponse(Exception):
    """Invalid response received from the API."""


class InvalidAPIKey(InvalidAPIResponse):
    """The API key was rejected because it is invalid, deactivated or expired."""


class TooManyRequests(Exception):
    """Too many requests, try again in 15 minutes."""


class FixedPriceRequired(InvalidAPIResponse):
    """A fixed-price product requires the customer's agreed electricity price."""
