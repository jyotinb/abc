{
    'name': 'Green2 Accessories - Foundation',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Foundation components for Green2 accessories system',
    'description': '''
        Green2 Accessories Foundation Module
        ====================================
        
        Manages foundation components for greenhouse structures:
        
        * Foundation Rod configurations
          - Rods per foundation
          - Rods per ASC pipe
        * Automatic calculation based on structure
        * Integration with main accessories framework
        
        Features:
        ---------
        * Enable/disable foundation rods
        * Configurable rods per foundation
        * Configurable rods per ASC pipe
        * Automatic calculation based on:
          - Number of foundations (columns)
          - Number of ASC pipes
        * Master data for foundation components
        * Cost calculation for foundation items
        
        Foundation Calculations:
        -----------------------
        * Foundation Rods = (Foundations × Rods per Foundation) + (ASC Pipes × Rods per ASC)
        * Foundations count from frame components
        * ASC pipes count from ASC components
    ''',
    'author': 'drkds',
    'website': 'http://www.drkdsinfo.com/',
    'depends': ['green2_accessories_base'],
    'data': [
        # Master Data
        'data/foundation_master_data.xml',
        
        # Views
        'views/green_master_foundation_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}