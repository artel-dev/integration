from datetime import date, datetime
from typing import Annotated
import re

from pydantic import BeforeValidator


def _empty_int_to_none(v):
    """Cleans string input by removing non-digit characters and handles empty/zero values."""
    cleaned_v = re.sub(r'\D', '', v) if isinstance(v, str) else v
    return cleaned_v if cleaned_v else None

def _empty_str_to_none(v):
    return None if v == "" else v

def _to_bool_validator(v):
    """Converts a string or int to a boolean. Other types are passed through."""
    if isinstance(v, str):
        return v.lower() == 'true'
    if isinstance(v, int):
        return v == 1
    return v

CleanInt = Annotated[int | None, BeforeValidator(_empty_int_to_none)]
OptionalDate = Annotated[date | None, BeforeValidator(_empty_str_to_none)]
OptionalDateTime = Annotated[datetime | None, BeforeValidator(_empty_str_to_none)]
StrBool = Annotated[bool, BeforeValidator(_to_bool_validator)]
