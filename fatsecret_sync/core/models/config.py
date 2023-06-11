import pathlib

from pydantic import BaseModel, Extra

from fatsecret_sync.api.models.auth import OAuth1Credentials, OAuth2Credentials


class FatSecretConfig(BaseModel):
    """
    API access credentials. Both are required to access the API, since
    FatSecret API calls use OAuth1 for one set of calls (food, branding, ), and OAuth2 for another.
    """

    oauth1: OAuth1Credentials
    oauth2: OAuth2Credentials


class TelegramConfig(BaseModel):
    admin_id: int | str
    bot_token: str


class FilesUserBackendConfig(BaseModel):
    name: str = "creds.yaml"
    root: pathlib.Path = "."
    user_isolation: bool = False


class UserBackendConfig(BaseModel):
    active: str = "files"
    files: FilesUserBackendConfig


class AppConfig(BaseModel):
    class Meta:
        extra = Extra.forbid

    fatsecret: FatSecretConfig
    telegram: TelegramConfig
    user_backend: UserBackendConfig
