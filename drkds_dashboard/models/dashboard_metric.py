from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re

class DrkdsDashboardMetric(models.Model):
    _name = 'drkds.dashboard.metric'
    _description = 'Dashboard Metrics'

    name = fields.Char(string='Metric Name', required=True)
    technical_name = fields.Char(string='Technical Name', required=True)
    model_name = fields.Char(string='Target Model', required=True)
    
    metric_type = fields.Selection([
        ('count', 'Record Count'),
        ('sum', 'Sum of Field'),
        ('avg', 'Average of Field'),
        ('custom', 'Custom Calculation')
    ], string='Metric Type', default='count', required=True)
    
    field_name = fields.Char(string='Field to Aggregate')
    python_code = fields.Text(string='Custom Calculation')
    
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)

    @api.model
    def create(self, vals):
        # Add validation logic
        if 'technical_name' not in vals:
            vals['technical_name'] = self._generate_technical_name(vals['name'])
        return super().create(vals)

    def _generate_technical_name(self, name):
        # Generate unique technical name
        technical_name = re.sub(r'\W+', '_', name.lower()).strip('_')
        base_name = technical_name
        counter = 1
        while self.search_count([('technical_name', '=', technical_name)]) > 0:
            technical_name = f"{base_name}_{counter}"
            counter += 1
        return technical_name

    def calculate_metric(self):
        # Metric calculation logic
        self.ensure_one()
        try:
            model = self.env[self.model_name]
            
            if self.metric_type == 'count':
                return model.search_count([])
            
            elif self.metric_type == 'sum':
                return sum(model.search([]).mapped(self.field_name))
            
            elif self.metric_type == 'avg':
                records = model.search([])
                return sum(records.mapped(self.field_name)) / len(records) if records else 0
            
            elif self.metric_type == 'custom':
                # Implement safe custom calculation
                return eval(self.python_code) if self.python_code else 0
        except Exception as e:
            return 0
            
