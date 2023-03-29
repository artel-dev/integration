from odoo import fields, models


class JiraWorklog(models.TransientModel):
    _name = 'ata.jira.worklog'
    _description = 'Jira worklog'

    name = fields.Char()
    exchange_id = fields.Many2one(comodel_name='ata.exchange')
    worklog_id = fields.Char()
    issue_id = fields.Char()
    comment = fields.Char()
    time_spent = fields.Float(digits=(15, 2))
    created_date = fields.Datetime()
    updated_date = fields.Datetime()
    started_date = fields.Datetime()
    author_name = fields.Char()
    author_display_name = fields.Char()
    author_email = fields.Char()
    author_avatar = fields.Binary()
    update_author_name = fields.Char()
    update_author_display_name = fields.Char()
    update_author_email = fields.Char()
