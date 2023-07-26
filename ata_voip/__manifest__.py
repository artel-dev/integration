{
    'name': 'VOIP customization',
    'summary': 'VOIP customization',
    'version': '16.0.1.0.1',
    'category': 'VOIP',
    'author': 'ToDo',
    'website': 'https://it-artel.ua',
    'license': 'OPL-1',
    'depends': ['base', 'voip', 'mail', 'web', 'web_mobile'],
    'installable': True,
    'application': True,
    'assets': {
        'mail.assets_messaging': [
            'ata_voip/static/src/models/*.js',
        ],
        'web.assets_backend': [
            'ata_voip/static/src/js/ata_phone_call_details.js',
        ],
    },
}
