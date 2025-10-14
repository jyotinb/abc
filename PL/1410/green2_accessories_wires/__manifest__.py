{
    'name': 'Green2 Accessories - Wires',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Wire and connector components for Green2 accessories system',
    'description': '''
        Green2 Accessories Wires Module
        ===============================
        
        Manages wire and connector components for greenhouse structures:
        
        * Zigzag Wire configurations
          - Multiple size options (1.4, 1.5, 1.6)
          - Automatic calculation based on profile length
        * Roll Up Connector configurations
          - Smooth connectors
          - Handle connectors
        * Integration with main accessories framework
        
        Features:
        ---------
        * Zigzag wire enable/disable toggle
        * Wire size selection (1.4mm, 1.5mm, 1.6mm)
        * Automatic wire length calculation based on total profile
        * Roll up connectors based on curtain count
        * Master data for all wire and connector types
        * Cost calculation for wires and connectors
        
        Wire Calculations:
        -----------------
        * Zigzag Wire: Based on total profile length
        * Roll Up Connectors: Based on number of curtains
          - Smooth: 1 per curtain
          - Handle: 1 per curtain
    ''',
    'author': 'drkds',
    'website': 'http://www.drkdsinfo.com/',
    'depends': ['green2_accessories_base'],
    'data': [
        # Master Data
        'data/wire_master_data.xml',
        
        # Views
        'views/green_master_wires_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}