from odoo import fields, models


class ExternalSystem(models.Model):
    """
    External system keeps datas about a connection to the server
    """
    _name = 'ata.external.system'
    _description = 'External system'

    name = fields.Char()
    description = fields.Char()
    server_address = fields.Char()
    server_port = fields.Integer()
    is_secure_connection = fields.Boolean()
    login = fields.Char()
    password = fields.Char()
    is_token_authentication = fields.Boolean()
    use_proxy = fields.Boolean()
    proxy_login = fields.Char()
    proxy_password = fields.Char()
    system_user_ids = fields.One2many(
        comodel_name='ata.external.system.user',
        inverse_name='system_id'
    )
