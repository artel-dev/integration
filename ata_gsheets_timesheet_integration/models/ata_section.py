from odoo import api, fields, models


class AtaSection(models.Model):
    _name = 'ata.section'

    name = fields.Char(string='Section')
