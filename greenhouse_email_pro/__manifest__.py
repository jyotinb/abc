{
    'name': 'Professional Greenhouse Email Marketing Pro',
    'version': '17.0.1.0.0',
    'category': 'Marketing',
    'summary': 'Professional Email Marketing for Greenhouse & Agriculture Businesses',
    'description': '''
        Professional Greenhouse Email Marketing System
        =============================================
        
        Specialized Features:
        * Anti-spam compliant email system
        * Greenhouse & agriculture template library
        * 500+ farming symbols & emojis
        * Agricultural automation themes
        * Seasonal growing campaign templates
        * GDPR & CAN-SPAM compliant
        * Professional greenhouse designs
        * Plant catalog templates
        * Growing season campaigns
        * Weather-based automation
        * Seed & harvest notifications
        * Equipment maintenance alerts
        
        Perfect for:
        * Greenhouse operations
        * Plant nurseries
        * Agricultural automation companies
        * Farming equipment suppliers
        * Seed & fertilizer distributors
        * Organic farming businesses
        * Hydroponic systems
        * Smart farming solutions
    ''',
    'author': 'Greenhouse Pro Team',
    'website': 'https://greenhouse-pro.com',
    'depends': ['base', 'mail', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'data/symbol_library.xml',
        'data/greenhouse_components.xml',
        'data/compliance_templates.xml',
        'views/email_template_views.xml',
        'views/email_campaign_views.xml',
        'views/contact_group_views.xml',
        'views/symbol_library_views.xml',
        'views/compliance_checker_views.xml',
        'wizards/template_builder_wizard_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}