{
    'name': 'Simple BOM Variant',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Apply BOM on Specific Product Variants',
    'description': '''
Simple BOM Variant Support
==========================

This module adds the "Apply on Variants" functionality to BOMs, allowing you to:
* Create BOMs that apply only to specific product variants
* Select which variants a BOM should be used for
* Maintain separate BOMs for different product variants

Simple and lightweight - no complex features, just the core functionality.
    ''',
    'author': 'Your Company',
    'depends': ['mrp'],
    'data': [
        'views/mrp_bom_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}