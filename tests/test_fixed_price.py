"""Fixed-price products retain the agreed net price in API requests."""

from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit

import pytest

from pystromligning import Stromligning
from pystromligning.exceptions import FixedPriceRequired


def client(product_type="fixed"):
    """Select a product and supplier without making network requests."""
    api = Stromligning()
    api.company = {"id": "fixed", "productType": product_type}
    api.supplier = {"id": "grid", "priceArea": "DK1"}
    return api


def test_product_types_are_preserved():
    """Product selection uses API metadata rather than product names."""
    api = client()
    api._get_response = Mock(
        return_value=[
            {
                "name": "Provider",
                "products": [
                    {"id": "fixed", "name": "Agreement", "productType": "fixed"},
                    {"id": "variable", "name": "Fastpris", "productType": "variable"},
                ],
            }
        ]
    )
    products = api._get_companies()
    assert [product["productType"] for product in products] == ["fixed", "variable"]


@pytest.mark.parametrize("price", [0, 0.8, 1.234567])
def test_fixed_price_request(price):
    """The supplied net price reaches the API without replacing other parameters."""
    api = client()
    api.set_electricity_price(price)
    api._get_response = Mock(return_value={"prices": []})
    api.update("2026-10-25T00:00:00.000Z")
    params = parse_qs(urlsplit(api._get_response.call_args.args[0]).query)
    assert float(params["electricityPrice"][0]) == price
    assert params["productId"] == ["fixed"]
    assert params["supplierId"] == ["grid"]
    assert params["aggregation"] == ["1h"]
    assert params["forecast"] == ["false"]


def test_missing_price_never_calls_api():
    """Missing agreement prices fail before using a network request."""
    api = client()
    api._get_response = Mock()
    with pytest.raises(FixedPriceRequired):
        api.update()
    api._get_response.assert_not_called()


def test_variable_product_ignores_previous_price():
    """A saved fixed price cannot override spot prices after switching products."""
    api = client("variable")
    api.set_electricity_price(1)
    api._get_response = Mock(return_value={"prices": []})
    api.update()
    assert "electricityPrice" not in api._get_response.call_args.args[0]
    api.set_electricity_price(None)
    assert api.electricity_price is None


@pytest.mark.parametrize("price", [-1, float("nan"), float("inf"), -float("inf")])
def test_invalid_amount(price):
    """Reject invalid amounts before they can become query parameters."""
    with pytest.raises(ValueError):
        client().set_electricity_price(price)


@pytest.mark.parametrize("price", [True, False, "1.25", {}, []])
def test_non_numeric_amount(price):
    """Booleans and text are not electricity prices."""
    with pytest.raises(TypeError):
        client().set_electricity_price(price)
