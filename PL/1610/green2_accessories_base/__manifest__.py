{
    'name': 'Green2 Accessories Base',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Base module for Green2 accessories management system',
    'description': '''
        Green2 Accessories Base Module
        ==============================
        
        Foundation module for the modular accessories system:
        
        * Core accessories framework and data models
        * Accessories master data management
        * Component line extensions for accessories
        * Base calculation methods for accessories
        * Section-wise component organization
        * Excel export framework for accessories
        * Cost calculation infrastructure
        
        This module provides:
        -----------------------
        * Accessories Master model for managing accessory types
        * Accessories Component Line for tracking accessory components  
        * Base fields and methods that will be extended by specific modules
        * Common utilities for accessory calculations
        * Excel export capabilities
        
        Other modules dependency structure:
        ------------------------------------
        - green2_accessories_brackets (for bracket components)
        - green2_accessories_clamps (for clamp components)
        - green2_accessories_wires (for wire & connector components)
        - green2_accessories_profiles (for profile components)
        - green2_accessories_foundation (for foundation components)
    ''',
    'author': 'drkds',
    'website': 'http://www.drkdsinfo.com/',
    'depends': ['green2_base'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Data
        'data/accessories_categories.xml',
        
        # Views
        'views/accessories_master_views.xml',
        'views/accessories_component_line_views.xml',
        'views/green_master_accessories_base_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}