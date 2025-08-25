# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import json
import logging

_logger = logging.getLogger(__name__)


class GreenhouseInputValue(models.Model):
    """Store user input values - like Excel input cells"""
    _name = 'greenhouse.input.value'
    _description = 'Greenhouse Input Value'
    _order = 'section_id, sequence, field_label'
    
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
    ], string='Field Type', default='float', required=True)
    
    # Value storage (everything stored as text, converted on access)
    value = fields.Char('Value', default='0')
    
    # UI helpers
    sequence = fields.Integer('Sequence', default=10)
    help_text = fields.Text('Help Text')
    is_required = fields.Boolean('Required', default=False)
    
    # Validation
    min_value = fields.Float('Min Value')
    max_value = fields.Float('Max Value')
    selection_options = fields.Text('Selection Options', help='JSON array of options')
    
    @api.model
    def create(self, vals):
        """Ensure required fields are set"""
        # Validate field_code
        if not vals.get('field_code'):
            raise ValidationError("Field Code is required")
        
        # Set default field_label if not provided
        if not vals.get('field_label'):
            vals['field_label'] = vals['field_code'].replace('_', ' ').title()
        
        # Set default value if not provided
        if 'value' not in vals or vals['value'] is None:
            field_type = vals.get('field_type', 'float')
            if field_type == 'boolean':
                vals['value'] = 'false'
            elif field_type == 'selection':
                # Get first option if available
                if vals.get('selection_options'):
                    try:
                        options = json.loads(vals['selection_options'])
                        vals['value'] = options[0] if options else '0'
                    except:
                        vals['value'] = '0'
                else:
                    vals['value'] = '0'
            else:
                vals['value'] = '0'
        
        return super().create(vals)
    
    @api.constrains('value', 'field_type')
    def _check_value(self):
        """Validate input value based on field type"""
        for record in self:
            if not record.value:
                continue
                
            if record.field_type == 'float':
                try:
                    val = float(record.value)
                    if record.min_value and val < record.min_value:
                        raise ValidationError(f"{record.field_label} must be at least {record.min_value}")
                    if record.max_value and val > record.max_value:
                        raise ValidationError(f"{record.field_label} must not exceed {record.max_value}")
                except ValueError:
                    raise ValidationError(f"{record.field_label} must be a number")
                    
            elif record.field_type == 'integer':
                try:
                    val = int(float(record.value))
                except ValueError:
                    raise ValidationError(f"{record.field_label} must be a whole number")
                    
            elif record.field_type == 'selection':
                if record.selection_options:
                    try:
                        options = json.loads(record.selection_options)
                        if record.value not in options:
                            raise ValidationError(f"{record.field_label} must be one of: {', '.join(options)}")
                    except json.JSONDecodeError:
                        pass
    
    def get_typed_value(self):
        """Return value in correct type"""
        self.ensure_one()
        if not self.value:
            # Return appropriate default based on type
            if self.field_type == 'float':
                return 0.0
            elif self.field_type == 'integer':
                return 0
            elif self.field_type == 'boolean':
                return False
            else:
                return ''
        
        try:
            if self.field_type == 'float':
                return float(self.value)
            elif self.field_type == 'integer':
                return int(float(self.value))
            elif self.field_type == 'boolean':
                return self.value.lower() in ('true', 'yes', '1')
            else:
                return self.value
        except (ValueError, TypeError):
            # Return safe defaults on conversion error
            if self.field_type in ('float', 'integer'):
                return 0
            elif self.field_type == 'boolean':
                return False
            else:
                return ''
    
    @api.onchange('value')
    def _onchange_value(self):
        """Mark project for recalculation and validate"""
        if self.project_id:
            self.project_id.needs_recalculation = True
        
        # Provide immediate feedback for validation
        if self.field_type == 'float' and self.value:
            try:
                val = float(self.value)
                if self.min_value and val < self.min_value:
                    return {
                        'warning': {
                            'title': 'Value Too Low',
                            'message': f'{self.field_label} should be at least {self.min_value}'
                        }
                    }
                if self.max_value and val > self.max_value:
                    return {
                        'warning': {
                            'title': 'Value Too High',
                            'message': f'{self.field_label} should not exceed {self.max_value}'
                        }
                    }
            except ValueError:
                return {
                    'warning': {
                        'title': 'Invalid Value',
                        'message': f'{self.field_label} must be a number'
                    }
                }
    
    @api.model
    def default_get(self, fields_list):
        """Set default section from context"""
        defaults = super().default_get(fields_list)
        if 'default_section_id' in self.env.context:
            defaults['section_id'] = self.env.context['default_section_id']
        return defaults
    
    def name_get(self):
        """Display name for input values"""
        result = []
        for record in self:
            name = record.field_label or record.field_code
            if record.section_id:
                name = f"[{record.section_id.code}] {name}"
            result.append((record.id, name))
        return result