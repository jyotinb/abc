{
    'name': 'Green2 Accessories - Brackets',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Bracket components for Green2 accessories system',
    'description': '''
        Green2 Accessories Brackets Module
        ==================================
        
        Manages bracket components for greenhouse structures:
        
        * Gutter Bracket configurations
          - Gutter Arch Bracket (HDGI 5.0 MM)
          - F Bracket (Big/Small)
        * Column Bracket configurations
          - L Bracket
          - Column Clamps
        * Automatic bracket calculation based on structure
        * Integration with main accessories framework
        
        Features:
        ---------
        * Gutter Bracket Type selection (Arch/F-Bracket/None)
        * Column Bracket Type selection (L-Bracket/Clamps/None)
        * Automatic calculation based on:
          - Number of spans and bays
          - Last span gutter configuration
          - Column configuration
        * Master data for all bracket types
        * Cost calculation for brackets
        
        Bracket Calculations:
        --------------------
        * Gutter Arch Brackets:
          - Full brackets: Based on spans and bays
          - Half brackets (left/right): For non-last span configurations
        * F Brackets:
          - Big: Based on big arch count
          - Small: Based on small arch count
        * L Brackets:
          - Quantity: 2 per middle column
        * Column Clamps:
          - Auto-detected pipe size
    ''',
    'author': 'drkds',
    'website': 'http://www.drkdsinfo.com/',
    'depends': ['green2_accessories_base'],
    'data': [
        # Master Data
        'data/bracket_master_data.xml',
        
        # Views
        'views/green_master_brackets_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}