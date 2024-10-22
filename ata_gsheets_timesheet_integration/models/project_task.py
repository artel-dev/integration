from odoo import _, api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'project.task'

    ata_section = fields.Selection(
        string='Section',
        selection=[
            ('all_sections', 'Всі розділи'),
            ('crm', 'CRM'),
            ('sales', 'Продажі'),
            ('procurement', 'Закупівлі'),
            ('storage', 'Склад'),
            ('production', 'Виробництво'),
            ('logistics', 'Логістика'),
            ('managerial_accounting', 'Управлінський облік'),
            ('accounting', 'Бухгалтерський облік'),
            ('personnel', 'Кадри'),
            ('recruiting', 'Рекрутинг'),
            ('salary', 'Заробітна плата'),
            ('marketing', 'Маркетинг'),
            ('projects', 'Проекти'),
            ('website', 'Веб-сайт'),
            ('repairs', 'Ремонти'),
            ('lms', 'LMS'),
            ('calendar', 'Календар'),
        ]
    )
    ata_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Project Manager'
    )
    ata_section_name = fields.Many2one(
        comodel_name='section.name',
        string='Section Name'
    )

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'project_id' in res:
            if res['project_id']:
                project_id = self.env['project.project'].browse(res['project_id'])
                project_manager = project_id.user_id
                res['ata_user_id'] = project_manager.id if project_manager else False
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'project_id' in vals and 'ata_user_id' not in vals:
                if vals['project_id']:
                    project_id = self.env['project.project'].browse(vals['project_id'])
                    project_manager = project_id.user_id
                    vals['ata_user_id'] = project_manager.id if project_manager else False
        res = super().create(vals_list)
        return res

    @staticmethod
    def open_section_wizard():
        message = _("Do you want to transfer data from a Section to a Section Name?")
        return {
            'name': 'Section Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'gsheet.timesheet.section.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'message': message,
            },
        }
