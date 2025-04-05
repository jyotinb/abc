from odoo import http
from odoo.http import request
import json

class DrkdsDashboardController(http.Controller):
    @http.route('/drkds_dashboard/get_metrics', type='json', auth='user', methods=['POST'])
    def get_dashboard_metrics(self, **params):
        """
        Fetch dashboard metrics
        """
        try:
            template_id = params.get('template_id')
            additional_domain = params.get('domain', [])
            
            if not template_id:
                return {
                    'success': False,
                    'error': 'Template ID is required'
                }
            
            # Get dashboard template
            template = request.env['drkds.dashboard.template'].browse(template_id)
            
            if not template.exists():
                return {
                    'success': False,
                    'error': 'Invalid template'
                }
            
            # Generate dashboard configuration
            dashboard_config = template.generate_dashboard_data(additional_domain)
            
            return {
                'success': True,
                'data': dashboard_config
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/drkds_dashboard/export', type='json', auth='user', methods=['POST'])
    def export_dashboard_data(self, **params):
        """
        Export dashboard data
        """
        try:
            template_id = params.get('template_id')
            export_format = params.get('format', 'csv')
            additional_domain = params.get('domain', [])
            
            if not template_id:
                return {
                    'success': False,
                    'error': 'Template ID is required'
                }
            
            # Get dashboard template
            template = request.env['drkds.dashboard.template'].browse(template_id)
            
            if not template.exists():
                return {
                    'success': False,
                    'error': 'Invalid template'
                }
            
            # Generate dashboard configuration
            dashboard_config = template.generate_dashboard_data(additional_domain)
            
            # Create export
            export = request.env['drkds.dashboard.export'].create_export(
                dashboard_config, 
                export_format
            )
            
            return {
                'success': True,
                'filename': export.file_name,
                'file_content': export.file_content.decode('utf-8'),
                'export_format': export_format
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }