import httpx

from anomaly_analyzer.core.config import settings
from anomaly_analyzer.core.domain_models.api import (
    JQuantsAuthResponse,
    JQuantsDailyQuotesResponse,
    JQuantsTokenResponse,
)


class JQuantsAPIClient:
    def __init__(self) -> None:
        self.base_url = "https://api.jquants.com/v1"
        self.mail_address = settings.jquants_mail_address
        self.password = settings.jquants_password
        self.refresh_token: str | None = None
        self.id_token: str | None = None

    async def _get_refresh_token(self) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/token/auth_user",
                json={"mailaddress": self.mail_address, "password": self.password},
            )
            response.raise_for_status()
            data = JQuantsAuthResponse.model_validate(response.json())
            return data.refresh_token

    async def _get_id_token(self, refresh_token: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/token/auth_refresh?refreshtoken={refresh_token}"
            )
            response.raise_for_status()
            data = JQuantsTokenResponse.model_validate(response.json())
            return data.id_token

    async def get_daily_quotes(
        self, code: str, pagination_key: str | None = None
    ) -> JQuantsDailyQuotesResponse:
        if not self.id_token:
            if not self.refresh_token:
                self.refresh_token = await self._get_refresh_token()
            self.id_token = await self._get_id_token(self.refresh_token)

        headers = {"Authorization": f"Bearer {self.id_token}"}
        params = {"code": code}
        if pagination_key:
            params["pagination_key"] = pagination_key

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/quotes/daily_quotes", headers=headers, params=params
            )

            if response.status_code in (401, 403):
                # Token might be expired, clear it and retry once
                self.id_token = None
                self.refresh_token = await self._get_refresh_token()
                self.id_token = await self._get_id_token(self.refresh_token)
                headers = {"Authorization": f"Bearer {self.id_token}"}
                response = await client.get(
                    f"{self.base_url}/quotes/daily_quotes",
                    headers=headers,
                    params=params,
                )

            response.raise_for_status()
            return JQuantsDailyQuotesResponse.model_validate(response.json())
