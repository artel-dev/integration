from typing import TypedDict, Optional
from datetime import datetime

from requests.structures import CaseInsensitiveDict
from requests_toolbelt import MultipartEncoder # type: ignore
from requests.auth import HTTPBasicAuth


class ExtResponse(TypedDict):
    result: str
    result_json: Optional[dict]
    status_code: Optional[int]
    error: bool
    error_msg: str
    start_date: Optional[datetime]
    finish_date: Optional[datetime]
    headers: CaseInsensitiveDict


class ExtRequestMethodParameters(TypedDict):
    # parameters for request.method()
    http_method: str
    url: str
    params: dict | MultipartEncoder
    request_body: str | dict | list
    headers: CaseInsensitiveDict
    auth: Optional[HTTPBasicAuth]
    token: str


class ExtRequest(TypedDict):
    # general
    name: Optional[str]
    create_date: datetime
    method_name: Optional[str]
    exchange_id: Optional[str]

    method_params: ExtRequestMethodParameters

    # execution parameters
    timeout: int
    is_executed: bool   # is request executed
    execution_date: Optional[datetime]
    is_processed: bool  # is request processed
    processing_date: Optional[datetime]

    response: Optional[ExtResponse]
