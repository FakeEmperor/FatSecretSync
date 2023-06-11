"""
FatSecret API implementation.
"""
import json
import logging
from typing import Any, NamedTuple, Optional, Type, TypeVar

import aiohttp
import oauthlib.oauth1
import pydantic
import yarl
from pydantic import BaseModel

from ..utils.oauth import oauth1_request, oauth1_token_request
from .errors import APIError, RequestError
from .models.auth import OAuth1Credentials, OAuth1UserFlowConfig, OAuth2Credentials
from .models.common import DateInt
from .models.errors import APIErrorResponse
from .models.food import FoodInfoV3
from .models.food_entry import CreateFoodEntryRequest, EditFoodEntryRequest, FoodEntries
from .models.profile import ProfileStatus

logger = logging.getLogger(__name__)

# API URLs
API_URL = "https://platform.fatsecret.com/rest/server.api"


RetT = TypeVar("RetT", bound=BaseModel)


class AuthorizationRequestContext(NamedTuple):
    url: yarl.URL
    request_token: str
    request_token_secret: str


async def oauth1_api_call(
    method: str,
    api_method: str,
    data: Optional[dict] = None,
    headers: Optional[dict] = None,
    *,
    api_url: yarl.URL,
    user_oauth_token: str,
    oauth_client: oauthlib.oauth1.Client,
    session: aiohttp.ClientSession,
    raise_for_status: bool = False,
) -> tuple[aiohttp.ClientResponse, Any]:
    data, res = await oauth1_request(
        method,
        url=api_url.update_query(format="json", oauth_token=user_oauth_token, method=api_method),
        data=data,
        headers=headers,
        oauth_client=oauth_client,
        session=session,
    )
    if raise_for_status:
        res.raise_for_status()
    # TODO: maybe do not use this call at all
    return res, json.loads(data)


class FatSecretAPI:
    def __init__(
        self,
        oauth1_creds: Optional[OAuth1Credentials],
        oauth2_creds: Optional[OAuth2Credentials],
        user_credentials: Optional[OAuth2Credentials] = None,
        *,
        api_url: yarl.URL | str = API_URL,
        oauth1_user_flow_config: OAuth1UserFlowConfig = OAuth1UserFlowConfig(),
    ):
        self._oauth1_creds = oauth1_creds
        self._oauth2_creds = oauth2_creds
        self._user_credentials = user_credentials

        self.api_url = yarl.URL(api_url)
        self.oauth1_user_flow_config = oauth1_user_flow_config

        self._user_api: Optional["FatSecretUserAPI"] = None

        if not self._oauth2_creds and not self._oauth1_creds:
            raise ValueError("No credentials were provided, cannot access API")

    @property
    def is_user_specified(self):
        return self._user_credentials is not None

    async def make_authorization_url(self) -> AuthorizationRequestContext:
        client = self._make_oauth1_client(self._oauth1_creds, None)
        async with aiohttp.ClientSession() as session:
            request_token_data = await oauth1_token_request(
                "GET",
                yarl.URL(self.oauth1_user_flow_config.request_token_url).with_query(
                    oauth_callback=self.oauth1_user_flow_config.callback_url or "oob"
                ),
                oauth_client=client,
                session=session,
            )
            logger.debug(f"User authorization request token: {request_token_data}")
            request_token = request_token_data.get("oauth_token")
            request_token_secret = request_token_data.get("oauth_token_secret")
            return AuthorizationRequestContext(
                yarl.URL(self.oauth1_user_flow_config.authorize_url).with_query(oauth_token=request_token),
                request_token,
                request_token_secret,
            )

    async def authorize_user(self, pin: str | int, request_context: AuthorizationRequestContext) -> OAuth2Credentials:
        client = self._make_oauth1_client(
            self._oauth1_creds,
            user_creds=OAuth2Credentials(
                client_id=request_context.request_token, client_secret=request_context.request_token_secret
            ),
            verifier=str(pin),
        )
        async with aiohttp.ClientSession() as session:
            auth_token_data = await oauth1_token_request(
                "GET",
                yarl.URL(self.oauth1_user_flow_config.access_token_url),
                oauth_client=client,
                session=session,
            )
            logger.debug(f"User authorization token: {auth_token_data}")
        return OAuth2Credentials(client_id=auth_token_data["oauth_token"], client_secret=auth_token_data["oauth_token_secret"])

    @classmethod
    def _make_oauth1_client(
        cls, app_creds: OAuth1Credentials, user_creds: Optional[OAuth2Credentials], verifier: Optional[str] = None
    ) -> oauthlib.oauth1.Client:
        return oauthlib.oauth1.Client(
            app_creds.consumer_key,
            client_secret=app_creds.consumer_secret,
            resource_owner_key=user_creds.client_id if user_creds else None,
            resource_owner_secret=user_creds.client_secret if user_creds else None,
            verifier=verifier,
        )

    @property
    def user_api(self) -> "FatSecretUserAPI":
        if not self._user_api:
            if not self._user_credentials:
                raise RuntimeError("User credentials are not provided. Cannot create user API.")
            self._user_api = FatSecretUserAPI(
                api=self,
                oauth_client=self._make_oauth1_client(app_creds=self._oauth1_creds, user_creds=self._user_credentials),
                user_credentials=self._user_credentials,
            )
        return self._user_api

    def get_user_api(self, user_credentials: OAuth2Credentials) -> "FatSecretUserAPI":
        return FatSecretUserAPI(
            api=self,
            oauth_client=self._make_oauth1_client(app_creds=self._oauth1_creds, user_creds=user_credentials),
            user_credentials=user_credentials,
        )


class FatSecretUserAPI:
    def __init__(self, api: FatSecretAPI, oauth_client: oauthlib.oauth1.Client, user_credentials: OAuth2Credentials):
        self.api = api
        self.oauth_client = oauth_client
        self.user_credentials = user_credentials

    @classmethod
    def _check_api_response(cls, call_name: str, response: aiohttp.ClientResponse, data: dict | list):
        if response.ok and data and "error" not in data:
            return
        if not data:
            raise RequestError("No data returned", method=response.method, call_name=call_name, response=response, details=data)
        try:
            error = APIErrorResponse.validate(data["error"])
        except (TypeError, ValueError, pydantic.ValidationError):
            raise RequestError(
                "Unexpected API response", method=response.method, call_name=call_name, response=response, details=data
            ) from None
        raise APIError("Failed API call", method=response.method, call_name=call_name, response=response, error=error)

    async def api_call(
        self, method: str, call_name: str, *, data: Optional[dict] = None, query: Optional[dict] = None
    ) -> tuple[aiohttp.ClientResponse, dict | list]:
        logger.debug(f"[{method} {call_name}] Calling with query={query}, data={data is not None}")
        url = self.api.api_url
        if query:
            url = url.update_query({k: v if not isinstance(v, DateInt) else int(v) for k, v in query.items() if v is not None})
        # logger.debug(f"[{method} {call_name}] Calling {url}")
        async with aiohttp.ClientSession() as session:
            res, res_data = await oauth1_api_call(
                "GET",
                call_name,
                user_oauth_token=self.user_credentials.client_id,
                oauth_client=self.oauth_client,
                session=session,
                data=data,
                api_url=url,
                raise_for_status=False,
            )
            logger.debug(f"[{method} {call_name}] Response code={res.status}, data={res_data is not None}")
            self._check_api_response(call_name=call_name, response=res, data=res_data)
        return res, res_data

    async def api_call_typed(
        self,
        method: str,
        call_name: str,
        response_type: Type[RetT],
        *,
        data: Optional[dict] = None,
        query: Optional[dict] = None,
        allow_none: bool = False,
    ) -> Optional[RetT]:
        field_name = call_name.split(".", maxsplit=1)[0]
        res, data = await self.api_call(method, call_name=call_name, data=data, query=query)
        ret_data = data[field_name]
        if ret_data is None:
            if allow_none:
                return None
            raise RequestError("Returned no data", method=method, call_name=call_name, response=res, details=data)
        return response_type.validate(ret_data)

    async def get_profile(self) -> ProfileStatus:
        """
        Link: https://platform.fatsecret.com/api/Default.aspx?screen=rapiref&method=profile.get

        Returns general status information for a nominated user.

        Returns:
            ProfileInfo instance
        """
        return await self.api_call_typed("GET", "profile.get", ProfileStatus)

    async def get_food_entries_v2(self, date: Optional[DateInt], food_entry_id: Optional[int] = None) -> Optional[FoodEntries]:
        """
        Link: https://platform.fatsecret.com/api/Default.aspx?screen=rapiref&method=food_entries.get.v2

        Returns saved food diary entries for the user according to the filter specified.
        This method can be used to return all food diary entries recorded on a nominated `date` or
        a single food diary entry with a `nominated food_entry_id`.

        Args:
            date:
                Date of food entries;
            food_entry_id:
                Concrete Food Entry ID;
        Returns:
            List of FoodEntry objects
        """
        if date is None and food_entry_id is None:
            raise ValueError("Invalid request parameters", "'date' or 'food_entry_id' must be specified")
        return await self.api_call_typed(
            "GET",
            "food_entries.get.v2",
            FoodEntries,
            query={"date": date.to_int() if date else None, "food_entry_id": food_entry_id},
            allow_none=True,
        )

    async def get_food_v3(self, food_id: int) -> FoodInfoV3:
        """
        Link: https://platform.fatsecret.com/api/Default.aspx?screen=rapiref&method=food.get.v3

        Returns detailed nutritional information for the specified food.
        Use this call to display nutrition values for a food to users.

        Args:
            food_id:
                The ID of the food to retrieve.
        Returns:
            The food element returned contains general information about the food item
            with detailed nutritional information for each available standard serving size.
        """
        return await self.api_call_typed("GET", "food.get.v3", FoodInfoV3, query={"food_id": food_id})

    async def create_entry(self, request: CreateFoodEntryRequest) -> int:
        """
        Link: https://platform.fatsecret.com/api/Default.aspx?screen=rapiref&method=food_entry.create

        Records a food diary entry for the user according to the parameters specified.

        Args:
            request:
                CreateFoodEntryRequest instance.
        Returns:
            The result of the call is the new unique identifier of the newly created food entry.
        """
        _, data = await self.api_call("GET", "food_entry.create", query=request.dict(exclude_none=True))
        return data["food_entry_id"]["value"]

    async def edit_entry(self, request: EditFoodEntryRequest) -> bool:
        """
        Link: https://platform.fatsecret.com/api/Default.aspx?screen=rapiref&method=food_entry.edit

        Adjusts the recorded values for a food diary entry.
        Note that the date of the entry may not be adjusted, however one or more of the other remaining properties:
         - food_entry_name
         - serving_id
         - number_of_units
         - meal
        may be altered.
        In order to shift the date for which a food diary entry was recorded
        the original entry must be deleted and a new entry recorded.

        Args:
            request:
                EditFoodEntryRequest instance.
        Returns:
            Success status of the edit operation.
        """
        _, data = await self.api_call("GET", "food_entry.edit", query=request.dict(exclude_none=True))
        return data["success"]["value"] == 1

    async def delete_entry(self, food_entry_id: int) -> bool:
        """
        Link: https://platform.fatsecret.com/api/Default.aspx?screen=rapiref&method=food.get.v3

        Records a food diary entry for the user according to the parameters specified.

        Args:
            food_entry_id:
                The ID of the food entry to delete.
        Returns:
            Success status of the edit operation.
        """
        _, data = await self.api_call("GET", "food_entry.delete", query={"food_entry_id": food_entry_id})
        return data["success"]["value"] == 1
