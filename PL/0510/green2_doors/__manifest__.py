{
    'name': 'Greenhouse Management - Door Components',
    'version': '17.0.1.0.0',
    'summary': 'Door components module for greenhouse management',
    'category': 'Manufacturing',
    'description': """
        Greenhouse Door Components Module
        =================================
        
        Manages door-related components:
        * Standalone Door configurations
        * Entry Chamber settings
        * Tractor Door configurations (Vertical/Openable)
        * Chamber depth and column settings
        * Door-specific length masters
        * Integration with structure calculations
    """,
    'author': 'drkds',
    'website': 'http://www.drkdsinfo.com/',
    'depends': ['green2_base'],
    'data': [
        'security/ir.model.access.csv',
        'data/door_length_data.xml',
        'views/green_master_door_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}