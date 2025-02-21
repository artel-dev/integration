from odoo import api, fields, models


class AtaSection(models.Model):
    _name = 'ata.section'
    _description = 'Section'

    name = fields.Char(string='Section')
