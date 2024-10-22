from odoo import api, fields, models


class SectionName(models.Model):
    _name = 'section.name'

    name = fields.Char(string='Section')
