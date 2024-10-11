"""Custom exceptions used in the pyStromligning library."""


class InvalidAPIResponse(Exception):
    """Invalid response received from the API."""


class TooManyRequests(Exception):
    """Too many requests, try again in 15 minutes."""
