import pytest
from httpx import Response

from anomaly_analyzer.core.api_client import JQuantsAPIClient


@pytest.mark.asyncio
async def test_get_daily_quotes(respx_mock):
    # Mock auth endpoints
    respx_mock.post("https://api.jquants.com/v1/token/auth_user").mock(
        return_value=Response(200, json={"refreshToken": "mock_refresh"})
    )
    respx_mock.post(
        "https://api.jquants.com/v1/token/auth_refresh?refreshtoken=mock_refresh"
    ).mock(return_value=Response(200, json={"idToken": "mock_id"}))

    # Mock quotes endpoint
    quotes_response = {
        "daily_quotes": [
            {
                "Date": "2023-01-04",
                "Code": "65990",
                "Open": 100.0,
                "High": 110.0,
                "Low": 90.0,
                "Close": 105.0,
                "Volume": 1000.0,
            }
        ]
    }
    respx_mock.get("https://api.jquants.com/v1/quotes/daily_quotes?code=65990").mock(
        return_value=Response(200, json=quotes_response)
    )

    client = JQuantsAPIClient()
    response = await client.get_daily_quotes(code="65990")

    assert len(response.daily_quotes) == 1
    assert response.daily_quotes[0].Code == "65990"
    assert response.daily_quotes[0].Open == 100.0


@pytest.mark.asyncio
async def test_get_daily_quotes_token_expiry_retry(respx_mock):
    # Mock auth endpoints
    respx_mock.post("https://api.jquants.com/v1/token/auth_user").mock(
        return_value=Response(200, json={"refreshToken": "mock_refresh"})
    )
    respx_mock.post(
        "https://api.jquants.com/v1/token/auth_refresh?refreshtoken=mock_refresh"
    ).mock(return_value=Response(200, json={"idToken": "mock_id_new"}))

    # First attempt fails with 401, second attempt succeeds
    quotes_route = respx_mock.get(
        "https://api.jquants.com/v1/quotes/daily_quotes?code=65990"
    )
    quotes_route.side_effect = [Response(401), Response(200, json={"daily_quotes": []})]

    client = JQuantsAPIClient()
    # Pre-set tokens to trigger 401 on first call
    client.refresh_token = "mock_refresh"
    client.id_token = "mock_id_old"

    response = await client.get_daily_quotes(code="65990")
    assert len(response.daily_quotes) == 0
    assert client.id_token == "mock_id_new"  # Verify token was refreshed
