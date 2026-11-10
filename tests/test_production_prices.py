"""Production prices use the selected grid supplier and shared settings."""

from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit

from pystromligning import Aggregation, Stromligning


def client():
    """Select a supplier without making network requests."""
    api = Stromligning()
    api.supplier = {"id": "radius_c", "priceArea": "DK2"}
    return api


def price(date, total):
    """Return a minimal production price entry."""
    return {"date": date, "price": {"value": total, "vat": 0, "total": total}}


def test_production_request_parameters():
    """The request carries supplier, start, aggregation and forecast settings."""
    api = client()
    api.set_forecast(True)
    api._get_response = Mock(return_value={"prices": []})
    api.update_production("2026-11-09T23:00:00.000Z")
    url = urlsplit(api._get_response.call_args.args[0])
    assert url.path == "/prices/production"
    assert parse_qs(url.query) == {
        "supplierId": ["radius_c"],
        "from": ["2026-11-09T23:00:00.000Z"],
        "aggregation": ["1h"],
        "forecast": ["true"],
    }


def test_production_native_resolution_omits_aggregation():
    """15-minute resolution uses the API's native resolution."""
    api = client()
    api.set_aggregation(Aggregation.MIN15)
    api._get_response = Mock(return_value={"prices": []})
    api.update_production("2026-11-09T23:00:00.000Z")
    query = parse_qs(urlsplit(api._get_response.call_args.args[0]).query)
    assert "aggregation" not in query
    assert query["forecast"] == ["false"]


def test_production_prices_are_sorted_and_deduplicated():
    """Prices are stored sorted by date without duplicates."""
    api = client()
    later = price("2026-11-10T00:00:00.000Z", 0.5)
    earlier = price("2026-11-09T23:00:00.000Z", 0.4)
    api._get_response = Mock(return_value={"prices": [later, earlier, later]})
    api.update_production("2026-11-09T23:00:00.000Z")
    assert api.production_prices == [earlier, later]
    assert api.prices == []
