# File: drkds_kit_calculator/__manifest__.py

{
    'name': 'DRKDS Kit Calculator',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Professional Kit Cost Calculator with Dynamic Templates',
    'description': '''
        Complete kit cost calculation system featuring:
        - Dynamic template-based calculations
        - Multi-level component management
        - Real-time cost updates
        - Professional quotation generation
        - User-friendly interface
        - Comprehensive reporting
    ''',
    'author': 'DRKDS Solutions',
    'website': 'https://www.drkds.com',
    'depends': ['base', 'web'],
    'data': [
        # Security (must be loaded first)
        'security/security.xml',
        'security/ir.model.access.csv',
        
        # Data (sequences and base data)
        'data/sequences.xml',
        'data/component_data.xml',
        'data/template_data.xml',
        
        # Views (in dependency order - no cross-references)
        'views/component_views.xml',
        'views/template_views.xml',
        'views/cost_sheet_views.xml',
        'views/dashboard_views.xml',
        'wizard/cost_calculator_wizard_views.xml',
        
        # Menu (references all actions - must be last)
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'drkds_kit_calculator/static/src/css/calculator.css',
            'drkds_kit_calculator/static/src/js/calculator.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}