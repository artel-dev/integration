from odoo import api, fields, models


class PlannedWorkloadReport(models.Model):
    _name = 'ata.planned.workload.report'
    _description = 'Planned workload report'
    _auto = False

    name = fields.Char()
    task_id = fields.Many2one(comodel_name='project.task')
    external_task_key = fields.Char()
    project_id = fields.Many2one(comodel_name='project.project')
    kanban_state = fields.Selection(
        selection=[
            ('normal', 'In Progress'),
            ('done', 'Ready'),
            ('blocked', 'Blocked')
        ],
        string='Status'
    )
    date_assign = fields.Datetime()
    date_end = fields.Datetime()
    assignees = fields.Char()
    planned_hours = fields.Float(digits=(10, 2))
    remaining_hours = fields.Float(digits=(10, 2))
    effective_hours = fields.Float(digits=(10, 2))

    @property
    def _table_query(self):
        query = f'{self._select()} {self._from()} {self._where()}'
        return query

    @api.model
    def _select(self):
        select_clause = """
            SELECT
                task.id AS id,
                task.name AS name,
                task.id AS task_id,
                task.external_task_key AS external_task_key,
                task.project_id AS project_id,
                task.kanban_state AS kanban_state,
                task.date_assign AS date_assign,
                task.date_end AS date_end,
                task.assignees AS assignees,
                task.planned_hours AS planned_hours,
                task.remaining_hours AS remaining_hours,
                task.effective_hours AS effective_hours
        """
        return select_clause

    @api.model
    def _from(self):
        from_clause = """
            FROM
                project_task AS task
        """
        return from_clause

    def _where(self):
        self.ensure_one()
        where_clause = """
            WHERE
                task.external_task_key NOT ISNULL
        """
        return where_clause
