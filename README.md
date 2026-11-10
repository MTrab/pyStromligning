![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)

## pyStromligning

This is a PyPI module for communicating with the Stromligning API, primarily developed for use with [Home Assistant](https://home-assistant.io), but I try to keep it as widely usable as possible.
## Fixed-price products

`available_companies` includes each product's `productType` (`fixed` or `variable`).
For fixed-price products, call `set_electricity_price(price)` with the customer's
agreed electricity price in kr/kWh **excluding VAT** before `update()`. The price
is sent as the documented `electricityPrice` parameter. Zero is supported;
negative, non-finite and non-numeric values are rejected. A missing price raises
`FixedPriceRequired` before a network request is made.

The catalogue's current `fixedPrice` is not used as the customer's agreed price.
Variable products omit `electricityPrice`, even if a price was previously set.
Use `set_electricity_price(None)` to clear the saved price.

API documentation: https://stromligning.dk/api/docs/

## User-Agent and API key

`Stromligning(dev=False, api_key=None, user_agent=None)`:

- `user_agent` identifies your application, for example `"MyApp/1.0"`. The
  library appends its own name and version, so requests are sent with
  `User-Agent: MyApp/1.0 pystromligning/<version>`. Without it the User-Agent is
  `pystromligning/<version>`.
- `api_key` is optional and sent as `Authorization: Bearer <key>`. Create a key
  at https://stromligning.dk/bruger/api-noegler. Requests with a key are rate
  limited per key instead of per IP address. Use `set_api_key(None)` to clear it.
  A rejected key (HTTP 401) raises `InvalidAPIKey`, a subclass of
  `InvalidAPIResponse`. The key is never logged.
