from odoo import api, fields, models


class AtaExchangeObjects(models.Model):
    """
    stored objects that need to be exchanged with external systems
    """
    _name = "ata.exchange.objects"
    _description = "Exchange objects with external systems"

    in_exchange = fields.Boolean()

    @api.model
    def add(self, records):
        records.ata_update_ext_system()
