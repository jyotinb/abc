{
    'name': 'Green2 Accessories - Clamps',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Advanced clamp components for Green2 accessories system',
    'description': '''
        Green2 Accessories Clamps Module
        ================================
        
        Comprehensive clamp management for greenhouse structures:
        
        * Advanced Clamp Types:
          - W Type Clamps
          - M Type Clamps  
          - Full Clamps
          - Half Clamps
          - L Joints
          - T Joints
        
        * Clamp Calculations for:
          - Bottom Chord connections
          - Big/Small Arch connections
          - V Support to Main Column
          - ASC Support connections
          - Border Purlin connections
          - Arch Middle Purlin
          - Cross Bracing connections
        
        * Features:
          - Auto size detection based on pipe configurations
          - Size override capability
          - Detailed calculation wizard with Excel export
          - Clamp accumulator for optimized grouping
          - Formula breakdown for transparency
        
        * Clamp Sizing:
          - Automatic detection from component pipe sizes
          - Support for round pipes (20mm to 114mm)
          - Support for square pipes
          - Manual size override option
        
        * Advanced Configurations:
          - Big/Small Purlin clamp type selections
          - Bottom chord clamp type (single/triple)
          - Border purlin clamp calculations
          - Anchor frame line considerations
    ''',
    'author': 'drkds',
    'website': 'http://www.drkdsinfo.com/',
    'depends': ['green2_accessories_base','green2_truss', 'green2_lower'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Master Data
        'data/clamp_master_data.xml',
        
        # Views
        'views/green_master_clamps_views.xml',
        
        # Wizard
        'wizard/clamp_calculation_detail_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}