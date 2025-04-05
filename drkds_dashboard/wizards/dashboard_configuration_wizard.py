from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re

class DrkdsDashboardConfigWizard(models.TransientModel):
    _name = 'drkds.dashboard.config.wizard'
    _description = 'Dashboard Configuration Wizard'

    configuration_mode = fields.Selection([
        ('metric', 'Create Metric'),
        ('filter', 'Create Filter'),
        ('template', 'Create Dashboard Template')
    ], string='Configuration Mode', required=True, default='metric')

    # Metric Fields
    metric_name = fields.Char(string='Metric Name')
    metric_model = fields.Selection('_get_available_models', string='Target Model')
    metric_type = fields.Selection([
        ('count', 'Record Count'),
        ('sum', 'Sum of Field'),
        ('avg', 'Average of Field'),
        ('custom', 'Custom Calculation')
    ], string='Metric Type')
    metric_field = fields.Char(string='Field to Aggregate')
    metric_domain = fields.Text(string='Filter Domain')
    metric_python_code = fields.Text(string='Custom Calculation')

    # Filter Fields
    filter_name = fields.Char(string='Filter Name')
    filter_model = fields.Selection('_get_available_models', string='Target Model')
    filter_type = fields.Selection([
        ('date_range', 'Date Range'),
        ('category', 'Category'),
        ('status', 'Status')
    ], string='Filter Type')
    filter_domain = fields.Text(string='Filter Domain')
    filter_metadata = fields.Text(string='Filter Metadata')

    # Template Fields
    template_name = fields.Char(string='Template Name')
    template_metrics = fields.Many2many('drkds.dashboard.metric', string='Metrics')
    template_filters = fields.Many2many('drkds.dashboard.filter', string='Filters')
    template_layout = fields.Text(string='Layout Configuration')
    template_description = fields.Text(string='Template Description')

    @api.model
    def _get_available_models(self):
        """
        Get list of available models for selection
        """
        return [
            ('sale.order', 'Sales Orders'),
            ('crm.lead', 'CRM Leads'),
            ('account.move', 'Accounting Moves'),
            ('hr.employee', 'Employees')
        ]

    def action_create_configuration(self):
        """
        Create configuration based on selected mode
        """
        self.ensure_one()
        
        try:
            if self.configuration_mode == 'metric':
                return self._create_metric()
            elif self.configuration_mode == 'filter':
                return self._create_filter()
            elif self.configuration_mode == 'template':
                return self._create_template()
        except Exception as e:
            raise ValidationError(f"Configuration creation failed: {str(e)}")

    def _create_metric(self):
        """
        Create a new dashboard metric
        """
        # Validate inputs
        if not self.metric_name or not self.metric_model or not self.metric_type:
            raise ValidationError("Please fill in all required metric fields")

        metric_vals = {
            'name': self.metric_name,
            'model_name': self.metric_model,
            'metric_type': self.metric_type,
            'field_name': self.metric_field,
            'python_code': self.metric_python_code,
            'domain': self.metric_domain or '[]'
        }

        metric = self.env['drkds.dashboard.metric'].create(metric_vals)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'drkds.dashboard.metric',
            'res_id': metric.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def _create_filter(self):
        """
        Create a new dashboard filter
        """
        # Validate inputs
        if not self.filter_name or not self.filter_model or not self.filter_type:
            raise ValidationError("Please fill in all required filter fields")

        filter_vals = {
            'name': self.filter_name,
            'model_name': self.filter_model,
            'filter_type': self.filter_type,
            'domain': self.filter_domain or '[]',
            'metadata': self.filter_metadata or '{}'
        }

        dashboard_filter = self.env['drkds.dashboard.filter'].create(filter_vals)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'drkds.dashboard.filter',
            'res_id': dashboard_filter.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def _create_template(self):
        """
        Create a new dashboard template
        """
        # Validate inputs
        if not self.template_name:
            raise ValidationError("Please provide a template name")

        template_vals = {
            'name': self.template_name,
            'description': self.template_description,
            'metric_ids': [(6, 0, self.template_metrics.ids)],
            'filter_ids': [(6, 0, self.template_filters.ids)],
            'layout_configuration': self.template_layout or '{}'
        }

        template = self.env['drkds.dashboard.template'].create(template_vals)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'drkds.dashboard.template',
            'res_id': template.id,
            'view_mode': 'form',
            'target': 'current'
        }