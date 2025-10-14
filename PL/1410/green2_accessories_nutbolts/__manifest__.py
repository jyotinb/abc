{
    'name': 'Green2 Accessories - Nut Bolts',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Nut-bolt and screw components for Green2 accessories system',
    'description': '''
        Green2 Accessories Nut-Bolts Module
        ===================================
        
        Manages nut-bolt and screw calculations for greenhouse structures.
    ''',
    'author': 'drkds',
    'website': 'http://www.drkdsinfo.com/',
    'depends': ['green2_accessories_base'],
    'data': [
        'security/ir.model.access.csv',
        'data/nutbolt_master_data.xml',
        'views/green_master_nutbolts_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
