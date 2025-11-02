{
    'name': 'Greenhouse Management - Frame Components',
    'version': '17.0.1.0.0',
    'summary': 'Frame components module for greenhouse management',
    'category': 'Manufacturing',
    'description': """
        Greenhouse Frame Components Module
        ==================================
        
        Manages frame-related components:
        * Column configurations (Main, Middle, Thick, Quadruple)
        * Anchor frame settings
        * Foundation calculations
        * Frame-specific length masters
    """,
    'author': 'drkds',
    'website': 'http://www.drkdsinfo.com/',
    'depends': ['green2_base'],
    'data': [
        'security/ir.model.access.csv',
        'data/frame_length_data.xml',
        'views/green_master_frame_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}