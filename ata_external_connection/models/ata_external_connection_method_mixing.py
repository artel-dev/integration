from odoo import fields, models


class AtaExternalConnectionMethodMixing(models.AbstractModel):
    _name = "ata.external.connection.method.mixing"
    _description = "Exchange http methods"

    method = fields.Selection(
        selection=[],
        string="Exchange http methods"
    )
