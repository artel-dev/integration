from odoo import fields, models


class JiraComment(models.TransientModel):
    _name = 'ata.jira.comment'
    _description = 'Jira comment'

    name = fields.Char()
    exchange_id = fields.Many2one(comodel_name='ata.exchange')
    comment_id = fields.Char()
    issue_id = fields.Char()
    body = fields.Char()
    comment_link = fields.Char()
    created_date = fields.Datetime()
    updated_date = fields.Datetime()
    author_name = fields.Char()
    author_display_name = fields.Char()
    author_email = fields.Char()
    update_author_name = fields.Char()
    update_author_display_name = fields.Char()
    update_author_email = fields.Char()
