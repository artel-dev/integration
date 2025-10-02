from datetime import date, datetime, timezone
from typing import Annotated
import re

from pydantic import AfterValidator, BeforeValidator


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

def _datetime_to_naive(v: datetime | None) -> datetime | None:
    """Converts timezone-aware datetime to naive datetime in UTC for Odoo compatibility."""
    if v is None:
        return None
    if isinstance(v, datetime) and v.tzinfo is not None:
        # Convert to UTC and remove timezone info
        return v.astimezone(timezone.utc).replace(tzinfo=None)
    return v

CleanInt = Annotated[int | None, BeforeValidator(_empty_int_to_none)]
OptionalDate = Annotated[date | None, BeforeValidator(_empty_str_to_none)]
OptionalDateTime = Annotated[datetime | None, BeforeValidator(_empty_str_to_none), AfterValidator(_datetime_to_naive)]
StrBool = Annotated[bool, BeforeValidator(_to_bool_validator)]
