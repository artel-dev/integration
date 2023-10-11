from odoo import fields, models


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
