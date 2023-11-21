from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ata_esputnik_token = fields.Char(
        string='eSputnik Token',
        config_parameter='ata_esputnik.token')
