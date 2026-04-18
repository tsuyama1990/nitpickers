from pydantic import BaseModel, ConfigDict, Field


class JQuantsAuthResponse(BaseModel):
    refresh_token: str = Field(alias="refreshToken")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class JQuantsTokenResponse(BaseModel):
    id_token: str = Field(alias="idToken")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class JQuantsQuote(BaseModel):
    Date: str
    Code: str
    Open: float | None = None
    High: float | None = None
    Low: float | None = None
    Close: float | None = None
    Volume: float | None = None

    model_config = ConfigDict(extra="ignore")


class JQuantsDailyQuotesResponse(BaseModel):
    daily_quotes: list[JQuantsQuote]
    pagination_key: str | None = None

    model_config = ConfigDict(extra="ignore")
