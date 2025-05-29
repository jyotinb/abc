from odoo import models, fields, api, _

class TemplateParameter(models.Model):
    _name = 'drkds.template.parameter'
    _description = 'Template Parameter Definition'
    _order = 'template_id, sequence, name'
    
    # Relations
    template_id = fields.Many2one('drkds.cost.template', string='Template',
                                required=True, ondelete='cascade')
    
    # Parameter Definition
    name = fields.Char(string='Parameter Name', required=True)
    code = fields.Char(string='Parameter Code', required=True,
                      help="Code used in formulas (e.g., 'length_8m')")
    parameter_type = fields.Selection([
        ('float', 'Number'),
        ('integer', 'Integer'),
        ('char', 'Text'),
        ('selection', 'Selection'),
        ('boolean', 'Yes/No')
    ], string='Parameter Type', required=True, default='float')
    
    # Configuration
    sequence = fields.Integer(string='Sequence', default=10)
    required = fields.Boolean(string='Required', default=True)
    default_value = fields.Char(string='Default Value')
    
    # For Selection Type
    selection_options = fields.Text(string='Selection Options',
                                   help="For selection type: option1,option2,option3")
    
    # Validation
    min_value = fields.Float(string='Minimum Value')
    max_value = fields.Float(string='Maximum Value')
    
    # Help
    description = fields.Text(string='Description')
    help_text = fields.Text(string='Help Text')

class CostParameter(models.Model):
    _name = 'drkds.cost.parameter'
    _description = 'Cost Sheet Parameter Value'
    _order = 'cost_sheet_id, sequence'
    
    # Relations
    cost_sheet_id = fields.Many2one('drkds.cost.sheet', string='Cost Sheet',
                                  required=True, ondelete='cascade')
    parameter_id = fields.Many2one('drkds.template.parameter', string='Parameter',
                                 required=True)
    
    # Parameter Details (Related)
    parameter_name = fields.Char(related='parameter_id.name', string='Parameter Name')
    parameter_code = fields.Char(related='parameter_id.code', string='Parameter Code')
    parameter_type = fields.Selection(related='parameter_id.parameter_type', string='Type')
    sequence = fields.Integer(related='parameter_id.sequence', string='Sequence')
    required = fields.Boolean(related='parameter_id.required', string='Required')
    
    # Values (based on parameter type)
    value_float = fields.Float(string='Float Value', digits=(12, 3))
    value_integer = fields.Integer(string='Integer Value')
    value_char = fields.Char(string='Text Value')
    value_selection = fields.Char(string='Selection Value')
    value_boolean = fields.Boolean(string='Boolean Value')
    
    # Computed Final Value
    final_value = fields.Char(string='Value', compute='_compute_final_value')
    
    @api.depends('parameter_type', 'value_float', 'value_integer', 'value_char', 
                 'value_selection', 'value_boolean')
    def _compute_final_value(self):
        for record in self:
            if record.parameter_type == 'float':
                record.final_value = str(record.value_float)
            elif record.parameter_type == 'integer':
                record.final_value = str(record.value_integer)
            elif record.parameter_type == 'char':
                record.final_value = record.value_char or ''
            elif record.parameter_type == 'selection':
                record.final_value = record.value_selection or ''
            elif record.parameter_type == 'boolean':
                record.final_value = str(record.value_boolean)
            else:
                record.final_value = ''
    
    def get_numeric_value(self):
        """Return numeric value for calculations"""
        if self.parameter_type == 'float':
            return self.value_float
        elif self.parameter_type == 'integer':
            return float(self.value_integer)
        elif self.parameter_type == 'boolean':
            return 1.0 if self.value_boolean else 0.0
        else:
            try:
                return float(self.final_value)
            except:
                return 0.0