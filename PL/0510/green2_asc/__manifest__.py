{
    'name': 'Greenhouse Management - ASC Components',
    'version': '17.0.1.0.0',
    'summary': 'ASC (Aerodynamic Side Corridors) module for greenhouse management',
    'category': 'Manufacturing',
    'description': """
        Greenhouse ASC Components Module
        ================================
        
        Manages ASC (Aerodynamic Side Corridors) components:
        * Front/Back Span ASC configurations
        * Front/Back Bay ASC configurations
        * Support Hockey settings
        * ASC Pipe calculations
        * ASC-specific length masters
        * Integration with Side Screen for hockey calculations
    """,
    'author': 'drkds',
    'website': 'http://www.drkdsinfo.com/',
    'depends': ['green2_base', 'green2_side_screen'],
    'data': [
        'security/ir.model.access.csv',
        'data/asc_length_data.xml',
        'views/green_master_asc_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}