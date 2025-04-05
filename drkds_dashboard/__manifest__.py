{
    'name': 'Drkds Dashboard',
    'version': '17.0.1.0.0',
    'category': 'Reporting',
    'summary': 'Comprehensive Dashboard Management System',
    'description': """
    Advanced dashboard module with:
    - Secure metric creation
    - Flexible filtering
    - Exportable dashboards
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': [
        'base', 
        'web', 
        'sale',
        'mail'
    ],
    'external_dependencies': {
        'python': ['xlsxwriter', 'reportlab'],
    },
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/dashboard_metric_views.xml',
        'views/dashboard_filter_views.xml',
        'views/dashboard_template_views.xml',
        'views/dashboard_export_views.xml',
        'wizards/dashboard_configuration_wizard_view.xml',
        'data/dashboard_metric_data.xml',
        'data/dashboard_template_data.xml',
        'data/dashboard_filter_data.xml',
        'data/dashboard_cron.xml',
        'views/assets.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'drkds_dashboard/static/src/css/dashboard.css',
            'drkds_dashboard/static/src/js/dashboard.js',
            'drkds_dashboard/static/src/js/chart_renderer.js',
            'drkds_dashboard/static/src/js/kpi_card.js',
            'drkds_dashboard/static/src/js/owl_sales_dashboard.js',
            'drkds_dashboard/static/src/xml/dashboard_template.xml',
            'drkds_dashboard/static/src/js/chart_renderer/chart_renderer.xml',
            'drkds_dashboard/static/src/js/kpi_card/kpi_card.xml',
            'drkds_dashboard/static/src/xml/owl_sales_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False
}
