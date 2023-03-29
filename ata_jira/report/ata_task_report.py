from odoo import api, fields, models


class TaskReport(models.Model):
    """
    Task report provides detail information about tasks and time sheets
    """
    _name = 'ata.task.report'
    _description = 'Task report'
    _order = 'timesheet_date, name'
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
    planned_hours = fields.Float(digits=(10, 2))
    employee_id = fields.Many2one(comodel_name='hr.employee')
    user_id = fields.Many2one(comodel_name='res.users')
    timesheet_date = fields.Date()
    timesheet_comment = fields.Char()
    worked_hours = fields.Float(digits=(10, 2))
    timesheet_count = fields.Integer()

    @property
    def _table_query(self):
        query = f'{self._select()} {self._from()} {self._where()}'
        return query

    @api.model
    def _select(self):
        select_clause = """
            SELECT
                timesheet.id AS id,
                task.name AS name,
                task.id AS task_id,
                task.external_task_key AS external_task_key,
                task.project_id AS project_id,
                task.kanban_state AS kanban_state,
                CASE
                    WHEN task.planned_hours ISNULL
                        THEN 0
                    ELSE task.planned_hours
                END AS planned_hours,
                timesheet.employee_id AS employee_id,
                timesheet.user_id AS user_id,
                timesheet.date AS timesheet_date,
                timesheet.name AS timesheet_comment,
                timesheet.unit_amount AS worked_hours,
                1 AS timesheet_count
        """
        return select_clause

    @api.model
    def _from(self):
        from_clause = """
            FROM
                project_task AS task
                INNER JOIN account_analytic_line AS timesheet
                ON task.id = timesheet.task_id
        """
        return from_clause

    @api.model
    def _where(self):
        where_clause = """
            WHERE
                NOT task.external_task_key ISNULL
        """
        return where_clause
