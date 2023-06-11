import aiohttp
from pydantic import BaseModel

from .models.errors import APIErrorResponse


class RequestError(Exception):
    def __init__(
        self,
        message: str,
        method: str,
        call_name: str,
        response: aiohttp.ClientResponse,
        details: BaseModel | dict | list | str,
        *args,
    ):
        super().__init__(message, method, call_name, response, details, *args)
        self.message = message
        self.method = method
        self.call_name = call_name
        self.response = response
        self.details = details


class APIError(RequestError):
    def __init__(
        self, message: str, method: str, call_name: str, response: aiohttp.ClientResponse, error: APIErrorResponse, *args
    ):
        super().__init__(message=message, method=method, call_name=call_name, response=response, details=error, *args)
        self.error = error
