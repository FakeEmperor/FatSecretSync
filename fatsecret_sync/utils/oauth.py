from typing import Optional
from urllib.parse import parse_qsl

import aiohttp
import oauthlib.common
import oauthlib.oauth1
import yarl


async def oauth1_request(
    method: str,
    url: yarl.URL | str,
    data: Optional[dict] = None,
    headers: Optional[dict] = None,
    *,
    oauth_client: oauthlib.oauth1.Client,
    session: aiohttp.ClientSession,
) -> tuple[bytes, aiohttp.ClientResponse]:
    request = oauthlib.common.Request(
        uri=str(url),
        http_method=method,
        body=data,
        headers=headers,
        encoding=oauth_client.encoding,
    )
    request.uri = str(yarl.URL(request.uri).update_query(dict(oauth_client.get_oauth_params(request))))
    signature = oauth_client.get_oauth_signature(request)
    async with session.request(
        method, yarl.URL(request.uri).update_query(oauth_signature=signature), data=data, headers=headers
    ) as res:
        return await res.read(), res


async def oauth1_token_request(
    method: str,
    url: yarl.URL | str,
    data: Optional[dict] = None,
    headers: Optional[dict] = None,
    *,
    oauth_client: oauthlib.oauth1.Client,
    session: aiohttp.ClientSession,
):
    # Parse the response to get the request token and token secret
    content, res = await oauth1_request(
        method=method, url=url, data=data, headers=headers, oauth_client=oauth_client, session=session
    )
    return dict(parse_qsl(content.decode()))
