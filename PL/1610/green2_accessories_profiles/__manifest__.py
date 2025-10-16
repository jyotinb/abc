{
    'name': 'Green2 Accessories - Profiles',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Profile calculations for Green2 accessories system',
    'description': '''
        Green2 Accessories Profiles Module
        ==================================
        
        Manages profile calculations for greenhouse structures:
        
        * Profile Types:
          - Profiles for Arch
          - Profile for Purlin
          - Profile for Bottom
          - Side Profile
          - Door Profile
          - Total Profile calculation
        
        Features:
        ---------
        * Automatic profile calculation based on structure
        * Profile breakdown by component type
        * Integration with zigzag wire calculations
        * Cost calculation for profiles
        * Master data for profile pricing
        
        Profile Calculations:
        --------------------
        * Profiles for Arch: Based on arch lengths and spans
        * Profile for Purlin: Based on purlin components
        * Profile for Bottom: Based on span length
        * Side Profile: Based on ASC and column configurations
        * Door Profile: Based on door components
        * Total Profile: Sum of all profile types
    ''',
    'author': 'drkds',
    'website': 'http://www.drkdsinfo.com/',
    'depends': ['green2_accessories_base'],
    'data': [
        # Master Data
        'data/profile_master_data.xml',
        
        # Views
        'views/green_master_profiles_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}