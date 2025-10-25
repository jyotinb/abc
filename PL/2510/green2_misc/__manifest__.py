{
    'name': 'Green2 Miscellaneous Components',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Miscellaneous components for Green2 system',
    'description': '''
        Green2 Miscellaneous Components Module
        ======================================
        
        Manages miscellaneous components:
        
        * Silicon - based on gutter type and configuration
        * Drainage Pipe - selectable lengths (6m/7m/8m)
        * Hose Clamp - based on funnel pipe size
        * Sliding Door - with door model selection
        
        Features:
        ---------
        * Silicon calculation based on IPPF gutter and last span gutter
        * Drainage pipe master data with selectable lengths
        * Door model master for sliding doors
        * Automatic component calculations
        * Integration with existing modules
    ''',
    'author': 'drkds',
    'website': 'http://www.drkdsinfo.com/',
    'depends': ['green2_accessories_base', 'green2_doors'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Master Data
        'data/misc_master_data.xml',
        
        # Views
        'views/green_master_misc_views.xml',
        'views/misc_master_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
