{
    'name': 'VOIP customization',
    'summary': 'VOIP customization',
    'version': '16.0.1.0.1',
    'category': 'VOIP',
    'author': 'ToDo',
    'website': 'https://it-artel.ua',
    'license': 'OPL-1',
    'depends': ['base', 'voip'],
    'data': [
       #'views/phonecall_views.xml',
    ],
    'qweb': [
        #'static/src/xml/ata_phone_call_details_override.xml',
    ],
    'js': [
       # 'static/src/js/ata_phone_call_details_override.js',
    ],
    'installable': True,
    'application': False,
    'assets': {
        'mail.assets_messaging': [
            'ata_voip/static/src/models/*.js',
        ],
    },
}
