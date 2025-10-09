{
    'name': 'Greenhouse Management - Truss Components',
    'version': '17.0.1.0.0',
    'summary': 'Truss components module for greenhouse management',
    'category': 'Manufacturing',
    'description': """
        Greenhouse Truss Components Module
        ==================================
        
        Manages truss-related components:
        * Big and Small Arch configurations
        * Bottom Chord settings (Anchor Frame & Inner Line)
        * V Support configurations
        * Arch Support (Big/Small)
        * Vent Support settings
        * Purlin configurations
        * Truss-specific length masters
    """,
    'author': 'drkds',
    'website': 'http://www.drkdsinfo.com/',
    'depends': ['green2_base', 'green2_frame'],
    'data': [
        'security/ir.model.access.csv',
        'data/truss_length_data.xml',
        'views/green_master_truss_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}