{
    'name': 'Green2 Accessories Management',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Excel-style accessories management for Green2 greenhouse system',
    'description': '''
        Green2 Accessories Management Module
        ===================================
        
        Excel-style accessories management with dynamic calculations:
        
        * Configurable accessory selections (Brackets, Wires, Connectors, Clamps)
        * Dynamic component generation based on structure parameters
        * Excel-style editable tables with inline editing
        * Automated cost calculations with configurable pricing
        * Integration with existing reports and Excel export
        * Auto-recalculation when main structure changes
        * Extensible framework for future accessory types
        
        Features:
        ---------
        * Gutter Bracket calculations (Arch/F-Bracket types)
        * Zigzag Wire calculations with size options
        * Column Bracket management (L-Bracket/Clamps)
        * Roll Up Connector calculations
        * Size auto-detection with manual override capability
        * Section-wise component organization
        * Professional reporting integration
    ''',
    'author': 'drkds',
    'website': 'http://www.drkdsinfo.com/',
    'depends': ['green2'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Master Data
        'data/accessories_master_data.xml',
        
        # Views
        'views/accessories_master_views.xml',
        'views/accessories_component_line_views.xml',
        'views/green_master_accessories_views.xml',
        
        # Reports
        'reports/accessories_report_template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}