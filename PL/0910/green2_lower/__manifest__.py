{
    'name': 'Greenhouse Management - Lower Section Components',
    'version': '17.0.1.0.0',
    'summary': 'Lower section components module for greenhouse management',
    'category': 'Manufacturing',
    'description': """
        Greenhouse Lower Section Components Module
        ==========================================
        
        Manages lower section components:
        * Cross Bracing configurations (Front/Back, Internal, Column-to-Arch, Column-to-Bottom)
        * Arch Middle Purlin settings
        * Gutter configurations (IPPF, Continuous)
        * Gutter accessories (End Cap, Funnel, Drainage Extension)
        * Lower section-specific length masters
    """,
    'author': 'drkds',
    'website': 'http://www.drkdsinfo.com/',
    'depends': ['green2_base', 'green2_frame', 'green2_truss'],
    'data': [
        'security/ir.model.access.csv',
        'data/lower_length_data.xml',
        'views/green_master_lower_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}