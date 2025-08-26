from odoo import models, fields, api
import json


class GreenhouseFieldTemplate(models.Model):
    _name = 'greenhouse.field.template'
    _description = 'Greenhouse Field Template'
    _order = 'section_id, sequence, name'

    # Basic Info
    name = fields.Char(string='Field Name', required=True)
    code = fields.Char(string='Field Code', required=True, help='Used in formulas')
    label = fields.Char(string='Display Label', required=True)
    section_id = fields.Many2one('greenhouse.section.template', required=True, ondelete='cascade')
    field_type = fields.Selection([
        ('input', 'Input Field'),
        ('calculated', 'Calculated Field')
    ], required=True, default='input')
    
    # Field Properties
    data_type = fields.Selection([
        ('float', 'Decimal Number'),
        ('integer', 'Whole Number'),
        ('char', 'Text'),
        ('boolean', 'True/False'),
        ('selection', 'Selection List')
    ], required=True, default='float')
    
    sequence = fields.Integer(string='Display Order', default=10)
    help = fields.Text(string='Help Text')
    active = fields.Boolean(string='Active', default=True)
    
    # Input Field Properties
    default_value = fields.Char(string='Default Value')
    required = fields.Boolean(string='Required Field', default=False)
    min_value = fields.Float(string='Minimum Value')
    max_value = fields.Float(string='Maximum Value')
    selection_options = fields.Text(
        string='Selection Options', 
        help='JSON format: ["option1", "option2", "option3"]'
    )
    
    # Calculated Field Properties  
    formula = fields.Text(string='Formula', help='Python expression with section.field references')
    length_per_unit = fields.Char(
        string='Length per Unit', 
        help='Formula for material quantity calculation'
    )
    
    @api.constrains('selection_options')
    def _check_selection_options(self):
        """Validate selection options JSON format"""
        for record in self:
            if record.data_type == 'selection' and record.selection_options:
                try:
                    options = json.loads(record.selection_options)
                    if not isinstance(options, list):
                        raise ValueError("Selection options must be a list")
                except (json.JSONDecodeError, ValueError) as e:
                    raise ValueError(f"Invalid selection options format: {e}")
    
    def get_selection_options_list(self):
        """Convert JSON selection options to list"""
        if self.selection_options:
            try:
                return json.loads(self.selection_options)
            except json.JSONDecodeError:
                return []
        return []
    
    _sql_constraints = [
        ('unique_section_code', 'unique(section_id, code)', 
         'Field code must be unique within section!')
    ]
