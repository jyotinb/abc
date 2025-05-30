# File: drkds_kit_calculator/__manifest__.py

{
    'name': 'DRKDS Kit Calculator',
    'version': '17.0.2.0.0',
    'category': 'Manufacturing',
    'summary': 'Professional Kit Cost Calculator with Advanced Formula Support',
    'description': '''
        Complete kit cost calculation system featuring:
        - Advanced template system with formula builder
        - Three types for parameters and components: Fixed, Input, Calculated
        - Interactive formula builder with field selection
        - Multi-level component management (Qty, Rate, Length)
        - Real-time cost updates and validation
        - Professional quotation generation
        - User-friendly interface with enhanced UX
        - Comprehensive reporting and analytics
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
        
        # Views (in dependency order)
        'views/component_views.xml',
        'views/template_views.xml',
        'views/cost_sheet_views.xml',
        'views/dashboard_views.xml',
        
        # Wizards
        'wizard/cost_calculator_wizard_views.xml',
        'wizard/formula_builder_wizard_views.xml',
        
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