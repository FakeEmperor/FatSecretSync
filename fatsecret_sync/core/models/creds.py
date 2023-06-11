import datetime

from kily.common.utils.dt import get_now
from pydantic import BaseModel, Field


class UserAuthInfo(BaseModel):
    obtained_at: datetime.datetime
    oauth_token: str
    oauth_token_secret: str


class UserBasicInfo(BaseModel):
    id: str
    name: str
    # noinspection Pydantic
    created_at: datetime.datetime = Field(default_factory=get_now)


class UserCreds(BaseModel):
    info: UserBasicInfo
    auth: UserAuthInfo


class CredsConfig(BaseModel):
    users: dict[str, UserCreds]
