from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json


class GreenhouseProjectData(models.Model):
    _name = 'greenhouse.project.data'
    _description = 'Greenhouse Project Data'
    _order = 'project_id, section_code, sequence, field_name'

    # Basic Info
    project_id = fields.Many2one('greenhouse.project', required=True, ondelete='cascade')
    section_code = fields.Char(string='Section Code', required=True)
    section_name = fields.Char(string='Section Name', required=True)
    field_code = fields.Char(string='Field Code', required=True)
    field_name = fields.Char(string='Field Name', required=True)
    label = fields.Char(string='Display Label', required=True)
    
    # Field Properties
    field_type = fields.Selection([
        ('input', 'Input Field'),
        ('calculated', 'Calculated Field')
    ], required=True)
    data_type = fields.Selection([
        ('float', 'Decimal Number'),
        ('integer', 'Whole Number'),
        ('char', 'Text'),
        ('boolean', 'True/False'),
        ('selection', 'Selection List')
    ], required=True)
    sequence = fields.Integer(string='Display Order', default=10)
    
    # Input Field Properties
    required = fields.Boolean(string='Required', default=False)
    default_value = fields.Char(string='Default Value')
    help = fields.Text(string='Help Text')
    
    # Values (based on data type)
    value_float = fields.Float(string='Float Value', digits=(16, 4))
    value_integer = fields.Integer(string='Integer Value')
    value_char = fields.Char(string='Text Value')
    value_boolean = fields.Boolean(string='Boolean Value')
    value_selection = fields.Char(string='Selection Value')
    
    # Calculated Field Properties
    formula = fields.Text(string='Formula')
    calculated_value = fields.Float(string='Calculated Result', digits=(16, 4))
    calculated_total_length = fields.Float(string='Total Length', digits=(16, 4))
    calculation_error = fields.Text(string='Calculation Error')
    
    # Computed field for unified value access
    display_value = fields.Char(string='Value', compute='_compute_display_value')
    
    # Add this field to the GreenhouseProjectData model
    unified_value = fields.Char(string='Value', compute='_compute_unified_value', inverse='_inverse_unified_value')

    @api.depends('data_type', 'value_float', 'value_integer', 'value_char', 'value_boolean', 'value_selection')
    def _compute_unified_value(self):
        """Compute unified value display based on data type"""
        for record in self:
            if record.data_type == 'float':
                record.unified_value = str(record.value_float) if record.value_float else ''
            elif record.data_type == 'integer':
                record.unified_value = str(record.value_integer) if record.value_integer else ''
            elif record.data_type == 'char':
                record.unified_value = record.value_char or ''
            elif record.data_type == 'boolean':
                record.unified_value = 'True' if record.value_boolean else 'False'
            elif record.data_type == 'selection':
                record.unified_value = record.value_selection or ''
            else:
                record.unified_value = ''

    def _inverse_unified_value(self):
        """Set appropriate value field based on data type"""
        for record in self:
            try:
                if record.data_type == 'float':
                    record.value_float = float(record.unified_value) if record.unified_value else 0.0
                elif record.data_type == 'integer':
                    record.value_integer = int(record.unified_value) if record.unified_value else 0
                elif record.data_type == 'char':
                    record.value_char = record.unified_value or ''
                elif record.data_type == 'boolean':
                    record.value_boolean = record.unified_value.lower() in ('true', '1', 'yes') if record.unified_value else False
                elif record.data_type == 'selection':
                    record.value_selection = record.unified_value or ''
            except (ValueError, AttributeError):
                # Handle conversion errors gracefully
                pass
        
    
    
    @api.depends('data_type', 'value_float', 'value_integer', 'value_char', 'value_boolean', 'value_selection', 'calculated_value')
    def _compute_display_value(self):
        """Compute display value based on data type"""
        for record in self:
            if record.field_type == 'calculated':
                record.display_value = str(record.calculated_value) if record.calculated_value else '0'
            elif record.data_type == 'float':
                record.display_value = str(record.value_float) if record.value_float else '0'
            elif record.data_type == 'integer':
                record.display_value = str(record.value_integer) if record.value_integer else '0'
            elif record.data_type == 'char':
                record.display_value = record.value_char or ''
            elif record.data_type == 'boolean':
                record.display_value = 'Yes' if record.value_boolean else 'No'
            elif record.data_type == 'selection':
                record.display_value = record.value_selection or ''
            else:
                record.display_value = ''
    
    def get_value(self):
        """Get the actual value based on data type"""
        self.ensure_one()
        
        if self.field_type == 'calculated':
            return self.calculated_value
            
        if self.data_type == 'float':
            return self.value_float or 0.0
        elif self.data_type == 'integer':
            return self.value_integer or 0
        elif self.data_type == 'char':
            return self.value_char or ''
        elif self.data_type == 'boolean':
            return self.value_boolean
        elif self.data_type == 'selection':
            return self.value_selection or ''
        
        return None
    
    def set_value(self, value):
        """Set value based on data type"""
        self.ensure_one()
        
        if self.data_type == 'float':
            self.value_float = float(value) if value else 0.0
        elif self.data_type == 'integer':
            self.value_integer = int(value) if value else 0
        elif self.data_type == 'char':
            self.value_char = str(value) if value else ''
        elif self.data_type == 'boolean':
            self.value_boolean = bool(value)
        elif self.data_type == 'selection':
            self.value_selection = str(value) if value else ''
    
    @api.model
    def create(self, vals):
        """Set default value on creation if provided"""
        record = super().create(vals)
        
        if record.field_type == 'input' and record.default_value:
            try:
                # Convert default value based on data type
                if record.data_type == 'float':
                    record.value_float = float(record.default_value)
                elif record.data_type == 'integer':
                    record.value_integer = int(record.default_value)
                elif record.data_type == 'char':
                    record.value_char = record.default_value
                elif record.data_type == 'boolean':
                    record.value_boolean = record.default_value.lower() in ('true', '1', 'yes')
                elif record.data_type == 'selection':
                    record.value_selection = record.default_value
            except (ValueError, AttributeError):
                # Ignore conversion errors for default values
                pass
        
        return record
    
    _sql_constraints = [
        ('unique_project_field', 'unique(project_id, section_code, field_code)', 
         'Field can only exist once per project section!')
    ]
