from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    external_project_key = fields.Char()
