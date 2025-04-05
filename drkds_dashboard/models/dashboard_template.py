from odoo import models, fields, api
from odoo.exceptions import ValidationError
import json
import logging

class DrkdsDashboardTemplate(models.Model):
    _name = 'drkds.dashboard.template'
    _description = 'Dashboard Templates'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Template Name', 
        required=True, 
        tracking=True,
        help="Name of the dashboard template"
    )
    
    description = fields.Text(
        string='Description', 
        tracking=True,
        help="Purpose and details of the dashboard template"
    )
    
    metric_ids = fields.Many2many(
        'drkds.dashboard.metric', 
        string='Included Metrics',
        help='Metrics included in this dashboard template'
    )
    
    filter_ids = fields.Many2many(
        'drkds.dashboard.filter', 
        string='Applied Filters',
        help='Filters applied to this dashboard template'
    )
    
    layout_configuration = fields.Text(
        string='Layout Configuration', 
        help='JSON configuration for dashboard layout'
    )
    
    active = fields.Boolean(default=True)
    
    # Tracking fields
    create_uid = fields.Many2one('res.users', string='Created By', readonly=True)

    @api.constrains('name', 'layout_configuration')
    def _validate_template_configuration(self):
        """
        Validate template configuration
        """
        for record in self:
            # Validate name
            if not record.name or len(record.name) < 3:
                raise ValidationError("Template name must be at least 3 characters long")
            
            # Validate layout configuration
            if record.layout_configuration:
                try:
                    json.loads(record.layout_configuration)
                except Exception:
                    raise ValidationError("Invalid layout configuration JSON")

    def generate_dashboard_configuration(self, additional_domain=None):
        """
        Generate comprehensive dashboard configuration
        """
        self.ensure_one()
        
        try:
            # Prepare dashboard configuration
            dashboard_config = {
                'name': self.name,
                'description': self.description,
                'metrics': {},
                'filters': {},
                'layout': json.loads(self.layout_configuration or '{}')
            }
            
            # Calculate metrics
            for metric in self.metric_ids:
                try:
                    dashboard_config['metrics'][metric.technical_name] = metric.calculate_metric(additional_domain)
                except Exception as e:
                    logging.error(f"Metric calculation error: {str(e)}")
                    dashboard_config['metrics'][metric.technical_name] = {
                        'error': str(e)
                    }
            
            # Apply filters
            applied_domain = []
            for dashboard_filter in self.filter_ids:
                try:
                    filter_domain = dashboard_filter.apply_filter()
                    applied_domain.extend(filter_domain)
                    dashboard_config['filters'][dashboard_filter.technical_name] = {
                        'name': dashboard_filter.name,
                        'domain': filter_domain
                    }
                except Exception as e:
                    logging.error(f"Filter application error: {str(e)}")
            
            return dashboard_config
        except Exception as e:
            logging.error(f"Dashboard configuration generation error: {str(e)}")
            raise ValidationError(f"Error generating dashboard configuration: {str(e)}")

    def action_preview_template(self):
        """
        Preview dashboard template configuration
        """
        self.ensure_one()
        
        try:
            config = self.generate_dashboard_configuration()
            
            # Prepare preview message
            metrics_count = len(config['metrics'])
            filters_count = len(config['filters'])
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': f'Template: {self.name}',
                    'message': f'Metrics: {metrics_count}, Filters: {filters_count}',
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Template Preview Error',
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }

    @api.model
    def create(self, vals):
        """
        Override create method with additional security checks
        """
        # Generate default layout if not provided
        if not vals.get('layout_configuration'):
            vals['layout_configuration'] = json.dumps({
                'type': 'grid',
                'columns': 3,
                'widgets': []
            })
        
        # Set creator
        vals['create_uid'] = self.env.user.id
        
        return super().create(vals)

    def write(self, vals):
        """
        Override write method with validation
        """
        # Validate layout configuration if provided
        if vals.get('layout_configuration'):
            try:
                json.loads(vals['layout_configuration'])
            except Exception:
                raise ValidationError("Invalid layout configuration JSON")
        
        return super().write(vals)