from pydantic import BaseModel, HttpUrl


class OAuth1Credentials(BaseModel):
    consumer_key: str
    consumer_secret: str


class OAuth2Credentials(BaseModel):
    client_id: str
    client_secret: str


OAUTH1_REQUEST_TOKEN_URL = "https://www.fatsecret.com/oauth/request_token"
OAUTH1_AUTHORIZE_URL = "https://www.fatsecret.com/oauth/authorize"
OAUTH1_ACCESS_TOKEN_URL = "https://www.fatsecret.com/oauth/access_token"


class OAuth1UserFlowConfig(BaseModel):
    request_token_url: HttpUrl = OAUTH1_REQUEST_TOKEN_URL
    authorize_url: HttpUrl = OAUTH1_AUTHORIZE_URL
    access_token_url: HttpUrl = OAUTH1_ACCESS_TOKEN_URL
    callback_url: HttpUrl | None = None
