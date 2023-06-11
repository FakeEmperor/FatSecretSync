"""
Common FatSecret error codes:
 - 2: Missing required oauth parameter: "<detail>"
 - 3: Unsupported oauth parameter: "<detail>"
 - 4: Invalid signature method: "<detail>"
 - 5: Invalid consumer key: "<detail>"
 - 6: Invalid/expired timestamp: "<detail>"
 - 7: Invalid/used nonce: "<detail>"
 - 8: Invalid signature: "<detail>"
 - 9: Invalid access token: "<detail>"
"""
from typing import Optional

from pydantic import BaseModel

KNOWN_ERROR_CODES = {
    2: "Missing required oauth parameter",
    3: "Unsupported oauth parameter",
    4: "Invalid signature method",
    5: "Invalid consumer key",
    6: "Invalid/expired timestamp",
    7: "Invalid/used nonce",
    8: "Invalid signature",
    9: "Invalid access token",
    101: "Missing required parameter",
    106: "Invalid ID",
    108: "Invalid Type",
}


class APIErrorResponse(BaseModel):
    code: int
    message: str

    @property
    def code_text(self) -> Optional[str]:
        return KNOWN_ERROR_CODES.get(self.code)
