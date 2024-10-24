from odoo import _, api, fields, models


class AtaProjectTask(models.Model):
    _inherit = 'project.task'

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'project_id' in res:
            if res['project_id']:
                project_id = self.env['project.project'].browse(res['project_id'])
                project_manager = project_id.user_id
                res['ata_user_id'] = project_manager.id if project_manager else False
        return res

    ata_section = fields.Selection(
        string='Section (Selection)',
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
    ata_section_id = fields.Many2one(
        comodel_name='ata.section',
        string='Section'
    )

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
