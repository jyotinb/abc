{
    'name': 'Green2 Accessories - Covering Material',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Covering material components for Green2 accessories system',
    'description': '''
        Green2 Accessories Covering Material Module
        ==========================================
        
        Manages covering material components for greenhouse structures:
        
        * Big Arch Plastic covering
        * Small Arch Plastic covering
        * Front and Back Span covering
        * Automatic covering material calculation
        * Width rounding to available standard widths
        * Apron and ASC considerations
        
        Features:
        ---------
        * Calculate Covering Material option
        * Big Arch Plastic: Length = Span Length + 1, Rolls = No of Spans
        * Small Arch Plastic: Length = Span Length + 1, Rolls = No of Spans
        * Front & Back Span: Length = Bay Length + 1, Rolls = 2
        * Width calculation based on:
          - Arch length rounded up to available widths
          - Apron configuration
          - ASC (Aerodynamic Side Corridors) presence
        * Master data for available covering widths
        * Cost calculation for covering materials
        
        Covering Calculations:
        ---------------------
        * Big Arch Plastic:
          - Length: Span Length + 1
          - Number of Rolls: Number of Spans
          - Width: Big Arch Length (rounded up to available width)
        
        * Small Arch Plastic:
          - Length: Span Length + 1
          - Number of Rolls: Number of Spans
          - Width: Small Arch Length (rounded up to available width)
        
        * Front and Back Span:
          - Length: Bay Length + 1
          - Number of Rolls: 2 (one for front, one for back)
          - Width: Depends on Apron and ASC configuration:
            * If Apron:
              - With ASC: ASC Length - 1
              - Without ASC: Column Length - 1
            * If No Apron:
              - With ASC: ASC Length + 0.5
              - Without ASC: Column Length + 0.5
    ''',
    'author': 'drkds',
    'website': 'http://www.drkdsinfo.com/',
    'depends': ['green2_accessories_base', 'green2_asc'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Master Data
        'data/covering_master_data.xml',
        
        # Views
        'views/green_master_covering_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
