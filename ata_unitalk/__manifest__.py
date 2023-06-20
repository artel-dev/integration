
{
    'name': 'UniTalks integration',
    'version': '1.0',
    'category': 'Customer Relationship Management',
    'description': 'Integration CRM with UniTalk',
    'category': 'Uncategorized',
    'depends': ['base', 'voip'],
    'data': [
       #'views/phonecall_views.xml',  # Файл з описом відображення для моделі
    ],
    'qweb': [
        'static/src/xml/ata_phone_call_details_override.xml',
    ],
    'js': [
        'static/src/js/ata_phone_call_details_override.js',
    ],
    'installable': True,
    'application': False,
}
