{
    'name': 'Greenhouse Management - Side Screen Components',
    'version': '17.0.1.0.0',
    'summary': 'Side screen components module for greenhouse management',
    'category': 'Manufacturing',
    'description': """
        Greenhouse Side Screen Components Module
        ========================================
        
        Manages side screen-related components:
        * Side Screen Roll Up Pipe and Joiner
        * Side Screen Guard configurations
        * Guard Box settings
        * Rollup Handles
        * Guard Spacer
        * Side screen-specific length masters
    """,
    'author': 'drkds',
    'website': 'http://www.drkdsinfo.com/',
    'depends': ['green2_base'],
    'data': [
        'security/ir.model.access.csv',
        'data/side_screen_length_data.xml',
        'views/green_master_side_screen_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}