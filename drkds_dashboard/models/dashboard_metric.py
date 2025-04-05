from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re
import logging
from odoo.tools.safe_eval import safe_eval
import time
import datetime

_logger = logging.getLogger(__name__)

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

    def calculate_metric(self, domain=None):
        # Metric calculation logic with improved security
        self.ensure_one()
        try:
            model = self.env[self.model_name]
            search_domain = domain or []
            
            if self.metric_type == 'count':
                return model.search_count(search_domain)
            
            elif self.metric_type == 'sum':
                records = model.search(search_domain)
                return sum(records.mapped(self.field_name)) if records else 0
            
            elif self.metric_type == 'avg':
                records = model.search(search_domain)
                values = records.mapped(self.field_name)
                return sum(values) / len(values) if values else 0
            
            elif self.metric_type == 'custom' and self.python_code:
                # Create safe execution context
                localdict = {
                    'env': self.env,
                    'model': model,
                    'domain': search_domain,
                    'user': self.env.user,
                    'time': time,
                    'datetime': datetime,
                    'sum': sum,
                    'len': len,
                    'result': None
                }
                
                # Execute code safely
                safe_eval(
                    "result = " + self.python_code,
                    localdict,
                    mode='exec',
                    nocopy=True
                )
                return localdict.get('result', 0)
            return 0
        except Exception as e:
            _logger.error(f"Error calculating metric {self.name}: {str(e)}")
            return 0
