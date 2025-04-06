from datetime import date, datetime
import json
from dateutil.parser import parse

from odoo import models


class AtaCustomFieldEncoderJSON(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime) or isinstance(o, date):
            return o.strftime("%Y-%m-%dT%H:%M:%S")
        return super().default(o)


class AtaExchangeJson(models.AbstractModel):
    _name = 'ata.exchange.json'
    _description = 'Convert json functions (ATA)'

    @staticmethod
    def parse_datetime(obj):
        for key, value in obj.items():
            if isinstance(value, str) and 'Date' in key:
                try:
                    obj[key] = parse(value)
                except ValueError:
                    pass
        return obj

    @staticmethod
    def parse_json_with_dates(json_str_in):
        json_str = json_str_in.decode() if isinstance(json_str_in, bytes) else json_str_in
        parsed_json = json.loads(json_str.lstrip('\ufeff'), object_hook=AtaExchangeJson.parse_datetime)
        return parsed_json

    @staticmethod
    def loads(json_str):
        return AtaExchangeJson.parse_json_with_dates(json_str)

    @staticmethod
    def dumps(data):
        return json.dumps(data, cls=AtaCustomFieldEncoderJSON)

    @staticmethod
    def convert_view(json_str: str|dict) -> str:
        try:
            if isinstance(json_str, dict):
                json_object = json.dumps(json_str, indent=4, ensure_ascii=False)
            else:
                json_object = json.loads(json_str.lstrip('\ufeff'), object_hook=AtaExchangeJson.parse_datetime)
                json_object = json.dumps(json_object, indent=4, ensure_ascii=False)

            return json_object
        except ValueError:
            return str(json_str)
