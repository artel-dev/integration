from odoo import fields, models


class ExternalSystemUser(models.Model):
    """
    External system user needs for keeping a login and password of user
    to a connection to the server
    """
    _name = 'ata.external.system.user'
    _description = 'External system user'

    name = fields.Char()
    system_id = fields.Many2one(comodel_name='ata.external.system')
    user_id = fields.Many2one(comodel_name='res.users')
    login = fields.Char()
    password = fields.Char()
