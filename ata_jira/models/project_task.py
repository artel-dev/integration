from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    external_task_key = fields.Char()
    assignee_list = fields.Char(compute='_compute_assignee_list', store=True)

    @api.depends('user_ids')
    def _compute_assignee_list(self):
        for obj in self:
            obj.assignee_list = ', '.join(
                sorted(list((user.name for user in obj.user_ids))))
