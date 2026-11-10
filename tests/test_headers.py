"""Requests identify the caller and send an optional API key."""

from unittest.mock import Mock, patch

import pytest

from pystromligning import LIBRARY_USER_AGENT, Stromligning
from pystromligning.exceptions import (
    InvalidAPIKey,
    InvalidAPIResponse,
    TooManyRequests,
)


def response(status=200, body=None):
    """Return a minimal requests response."""
    return Mock(status_code=status, json=Mock(return_value=body or {}))


def headers_for(api):
    """Make one request and return the headers it was sent with."""
    with patch("pystromligning.requests.get", return_value=response()) as get:
        api._get_response("/suppliers")
    assert get.call_args.kwargs["timeout"] == 60
    return get.call_args.kwargs["headers"]


def test_default_user_agent_without_key():
    """Anonymous requests identify the library and send no Authorization."""
    headers = headers_for(Stromligning())
    assert headers == {"User-Agent": LIBRARY_USER_AGENT}
    assert LIBRARY_USER_AGENT.startswith("pystromligning")


def test_application_user_agent_and_key():
    """The caller's product precedes the library and the key is a bearer token."""
    api = Stromligning(api_key=" secret ", user_agent="HomeAssistant-Stromligning/1.2")
    assert headers_for(api) == {
        "User-Agent": f"HomeAssistant-Stromligning/1.2 {LIBRARY_USER_AGENT}",
        "Authorization": "Bearer secret",
    }


@pytest.mark.parametrize("key", [None, "", "   "])
def test_blank_key_is_cleared(key):
    """Clearing or blanking the key returns to anonymous requests."""
    api = Stromligning(api_key="secret")
    api.set_api_key(key)
    assert "Authorization" not in headers_for(api)


def test_non_string_key_is_rejected():
    """Only strings are accepted as API keys."""
    with pytest.raises(TypeError):
        Stromligning(api_key=123)


def test_dev_api_url():
    """The development flag still selects the staging API."""
    with patch("pystromligning.requests.get", return_value=response()) as get:
        Stromligning(True)._get_response("/suppliers")
    assert get.call_args.args[0] == "https://staging.stromligning.dk/api/suppliers"


@pytest.mark.parametrize(
    "status,error",
    [(401, InvalidAPIKey), (429, TooManyRequests), (500, InvalidAPIResponse)],
)
def test_error_statuses(status, error):
    """A rejected key is distinguishable but remains an InvalidAPIResponse."""
    with (
        patch("pystromligning.requests.get", return_value=response(status)),
        pytest.raises(error),
    ):
        Stromligning(api_key="secret")._get_response("/suppliers")
    assert issubclass(InvalidAPIKey, InvalidAPIResponse)


def test_key_is_not_in_repr_or_logs(caplog):
    """The key is not written to debug logs."""
    caplog.set_level("DEBUG")
    api = Stromligning(api_key="secret")
    headers_for(api)
    assert "secret" not in caplog.text
