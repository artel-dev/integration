from datetime import datetime
import json
from dateutil.parser import parse

from odoo import models


class AtaCustomFieldEncoderJSON(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%dT%H:%M:%S")
        return super().default(obj)


class AtaJson(models.AbstractModel):
    _name = 'ata_external_connection.ata_json'
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
    def parse_json_with_dates(json_str):
        parsed_json = json.loads(json_str, object_hook=AtaJson.parse_datetime)
        return parsed_json

    @staticmethod
    def loads(json_str):
        return AtaJson.parse_json_with_dates(json_str)

    @staticmethod
    def dumps(data):
        return json.dumps(data, cls=AtaCustomFieldEncoderJSON)
