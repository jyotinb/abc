{
    'name': 'DRKDS Doors - Enhanced Green2 Extension',
    'version': '17.0.2.0.0',
    'category': 'Manufacturing',
    'summary': 'Enhanced door extension with structural components for Green2',
    'description': """
    Enhanced Door Management Extension for Green2
    ============================================
    
    Updated with specific structural components:
    * Standalone Doors: Column Pipe + Purlin Pipe per door
    * Entry Chambers: Front Columns + Purlins per chamber
    * Simplified configuration with essential parameters only
    * Formula: Door Components = X + Y, Chamber Components = Y
    """,
    'author': 'drkds',
    'website': 'http://www.drkdsinfo.com/',
    'depends': ['green2'],
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