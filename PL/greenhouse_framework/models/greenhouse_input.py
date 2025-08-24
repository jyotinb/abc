# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import json

class GreenhouseInputValue(models.Model):
    """Store user input values - like Excel input cells"""
    _name = 'greenhouse.input.value'
    _description = 'Greenhouse Input Value'
    _order = 'sequence, field_label'
    
    project_id = fields.Many2one(
        'greenhouse.project',
        string='Project',
        required=True,
        ondelete='cascade'
    )
    
    section_id = fields.Many2one(
        'greenhouse.section.template',
        string='Section'
    )
    
    # Field definition
    field_code = fields.Char('Field Code', required=True)
    field_label = fields.Char('Field Label', required=True)
    field_type = fields.Selection([
        ('float', 'Number'),
        ('integer', 'Whole Number'),
        ('selection', 'Dropdown'),
        ('boolean', 'Yes/No'),
        ('text', 'Text')
    ], string='Field Type', default='float')
    
    # Value storage (everything stored as text, converted on access)
    value = fields.Char('Value')
    
    # UI helpers
    sequence = fields.Integer('Sequence', default=10)
    help_text = fields.Text('Help Text')
    is_required = fields.Boolean('Required')
    
    # Validation
    min_value = fields.Float('Min Value')
    max_value = fields.Float('Max Value')
    selection_options = fields.Text('Selection Options', help='JSON array of options')
    
    @api.constrains('value')
    def _check_value(self):
        """Validate input value"""
        for record in self:
            if record.field_type == 'float' and record.value:
                try:
                    val = float(record.value)
                    if record.min_value and val < record.min_value:
                        raise ValidationError(f"{record.field_label} must be at least {record.min_value}")
                    if record.max_value and val > record.max_value:
                        raise ValidationError(f"{record.field_label} must not exceed {record.max_value}")
                except ValueError:
                    raise ValidationError(f"{record.field_label} must be a number")
    
    def get_typed_value(self):
        """Return value in correct type"""
        self.ensure_one()
        if not self.value:
            return None
            
        if self.field_type == 'float':
            return float(self.value)
        elif self.field_type == 'integer':
            return int(float(self.value))
        elif self.field_type == 'boolean':
            return self.value.lower() in ('true', 'yes', '1')
        else:
            return self.value
    
    @api.onchange('value')
    def _onchange_value(self):
        """Mark project for recalculation"""
        if self.project_id:
            self.project_id.needs_recalculation = True
