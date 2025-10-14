{
    'name': 'Green2 Accessories - Profile Calculations',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Accessories profile calculations for Green2 greenhouse management',
    'description': '''
        Green2 Accessories Module
        =========================
        
        This module extends Green2 with accessories profile calculations:
        
        * Profiles For Arch calculations
        * Profile For Purlin calculations  
        * Profile for Bottom calculations
        * Side Profile calculations
        * Door Profile calculations (from doors module)
        * Total Profile summation
        * Enhanced PDF report with accessories breakdown
        
        Dependencies:
        - green2 (base greenhouse module)
        - drkds_doors_v2 (doors extension)
    ''',
    'author': 'drkds',
    'website': 'http://www.drkdsinfo.com/',
    'depends': ['green2', 'drkds_doors_v2'],
    'data': [
        'security/ir.model.access.csv',
        'views/green_master_accessories_views.xml',
        'reports/accessories_report_template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}