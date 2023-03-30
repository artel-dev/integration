
{
    'name': 'UniTalk Operator',
    'version': '1.0',
    'category': 'Customer Relationship Management',
    'description': 'Integration CRM with UniTalk',
    'depends': ['crm', 'calendar'],
    'installable': True,
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'wizard/ata_unitalk_operator_views.xml',
        'wizard/ata_unitalk_operator_history_calls.xml',
        'views/ata_unitalk_operator_menu.xml',
        'views/ata_unitalk_operator_incalls.xml',
        # 'views/ata_unitalk_operator_history_calls.xml'
    ]
}
