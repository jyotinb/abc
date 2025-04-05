from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re
import json

class DrkdsDashboardFilter(models.Model):
    _name = 'drkds.dashboard.filter'
    _description = 'Dashboard Filters'

    name = fields.Char(string='Filter Name', required=True)
    technical_name = fields.Char(string='Technical Name', required=True)
    model_name = fields.Char(string='Target Model', required=True)
    
    filter_type = fields.Selection([
        ('date_range', 'Date Range'),
        ('category', 'Category'),
        ('status', 'Status')
    ], string='Filter Type', required=True)
    
    domain = fields.Text(string='Filter Domain')
    metadata = fields.Text(string='Filter Metadata')
    
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)

    @api.model
    def create(self, vals):
        # Generate technical name if not provided
        if 'technical_name' not in vals:
            vals['technical_name'] = self._generate_technical_name(vals['name'])
        
        # Validate domain and metadata
        if vals.get('domain'):
            self._validate_domain(vals['domain'])
        
        if vals.get('metadata'):
            self._validate_metadata(vals['metadata'])
        
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

    def _validate_domain(self, domain):
        # Basic domain validation
        try:
            domain_list = eval(domain)
            if not isinstance(domain_list, list):
                raise ValidationError("Domain must be a list of tuples")
        except Exception:
            raise ValidationError("Invalid domain format")

    def _validate_metadata(self, metadata):
        # Validate metadata JSON
        try:
            json.loads(metadata)
        except Exception:
            raise ValidationError("Invalid metadata JSON")

    def apply_filter(self, base_domain=None):
        # Apply filter to existing domain
        self.ensure_one()
        domain = base_domain or []
        
        if self.domain:
            filter_domain = eval(self.domain)
            domain.extend(filter_domain)
        
        return domain