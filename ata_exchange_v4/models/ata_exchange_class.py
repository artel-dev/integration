from odoo import api, models

from functools import wraps
from datetime import date, datetime
import logging

from .ata_exchange_method import AtaExchangeMethod
from odoo.addons.mail.models.mail_thread import MailThread

_logger = logging.getLogger(__name__)


class AtaExchangeClass(models.AbstractModel):
    _name = "ata.exchange.class"
    _description = "Exchange class extension"

    @staticmethod
    def ata_exchange_get_data_record_format(always_list=False):
        def decorator(func):
            @wraps(func)
            def wrapper(self: AtaExchangeClass, *args, **kwargs):
                data = func(self, *args, **kwargs)
                if data is None or not isinstance(data, list):
                    return data

                if always_list or not data:
                    out = data if data else ""
                else:
                    if len(data) == 0:
                        out = ""
                    elif len(data) == 1:
                        out = data[0]
                    else:
                        out = data

                return out
            return wrapper
        return decorator

    @staticmethod
    def _str_empty(value):
        if value:
            if isinstance(value, datetime):
                return value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, date):
                return value.strftime("%Y-%m-%d 00:00:00")
            else:
                return str(value)
        else:
            return ''

    #region overload outgoingdata methods
    def ata_exchange_compute_methods(self) -> list[AtaExchangeMethod]:
        return []

    def ata_exchange_validate(self, method: AtaExchangeMethod) -> list[str]:
        """
        Validate the record before exchange.

        This method is intended to be overridden in subclasses to implement
        specific validation logic for different models.
        It should return a list of error messages if validation fails,
        or an empty list if validation is successful.

        :param method: The exchange method being processed.
        :return: A list of validation error messages.
        """
        return []

    def ata_exchange_get_data_record(self, method: AtaExchangeMethod|None = None, as_node = False) -> list[dict]|dict|str:
        return {}

    @property
    def exchange_data(self) -> list[dict]|dict|str:
        return self.ata_exchange_get_data_record(method=None, as_node=False)

    #endregion

    #region enqueue event
    @api.model_create_multi
    def create(self, vals_list):
        records = self.env[self._name]
        for vals in vals_list:
            record = super().create([vals])
            records |= record
            if record._ata_exchange_check_add_to_queue(vals):
                record.ata_exchange_add_to_queue()

        return records

    def write(self, vals):
        over_write = super().write(vals)
        for record in self:
            if record._ata_exchange_check_add_to_queue(vals):
                record.ata_exchange_add_to_queue()
        return over_write

    def _ata_exchange_check_add_to_queue(self, vals: dict) -> bool:
        return True
        # return bool(self.ATA_EXCHANGE_NODE_NAME)
            
    def ata_exchange_add_to_queue(self):
        for record in self:
            self.env['ata.exchange.queue'].add_to_queue(record)
    #endregion

    #region outgoingdata methods
    def ata_exchange_notification(self, message: str, type: str = "mail.mt_note"):
        # TODO move to the functions of Method and processed there
        for record in self:
            if isinstance(record, MailThread):
                record.message_post(
                    body = message,
                    subtype_xmlid = type)
    
    def ata_exchange_get_ref_from_record(self) -> str|None:
        self.ensure_one()
        return "%s,%s" % (self._name, self.id) if self else None

    def ata_exchange_validate_main(self, method: AtaExchangeMethod) -> bool:
        # перевірка заповненості полів в екземплярі моделі
        result = self.ata_exchange_validate(method)
        if method.notification_validation and result:
            self.ata_exchange_notification(
                "Validation error when queuing exchange:<br/><ul><li>%s</li></ul>"
                % "</li><br/><li>".join(result))
                
        return not result

    def ata_exchange_get_request_data(self, method: AtaExchangeMethod) -> list[dict]|dict|str:
        # as_node - якщо запитуємо дані для кореневої ноди, то в залежності від статусу об'єкта
        # пакет даних може бути пустим. Це робиться для зменшення розміру пакетів обміну
        return data if (data:=self.ata_exchange_get_data_record(method = method, as_node = True)) else {}
    
    def ata_exchange_get_name(self) -> str:
        return f'{self._name} ({self.id}), {"name" in self._fields and self["name"]}' \
            if isinstance(self, models.Model) else ''
    
    #endregion
