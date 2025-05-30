# File: drkds_kit_calculator/models/template.py

from odoo import models, fields, api, _

class KitTemplate(models.Model):
    _name = 'kit.template'
    _description = 'Kit Template'
    _order = 'name'
    
    name = fields.Char(string='Template Name', required=True)
    code = fields.Char(string='Template Code', required=True)
    template_type = fields.Selection([
        ('nvph_8x4', 'NVPH 8x4'),
        ('nvph_9x4', 'NVPH 9.6x4'),
        ('rack_pinion', 'Rack and Pinion'),
        ('custom', 'Custom')
    ], string='Template Type', required=True, default='custom')
    
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    
    # Template lines
    component_ids = fields.One2many('kit.template.line', 'template_id', string='Components')
    parameter_ids = fields.One2many('kit.template.parameter', 'template_id', string='Parameters')
    
    # Computed fields
    component_count = fields.Integer(string='Components', compute='_compute_counts')
    parameter_count = fields.Integer(string='Parameters', compute='_compute_counts')
    
    @api.depends('component_ids', 'parameter_ids')
    def _compute_counts(self):
        for record in self:
            record.component_count = len(record.component_ids)
            record.parameter_count = len(record.parameter_ids)

class KitTemplateLine(models.Model):
    _name = 'kit.template.line'
    _description = 'Kit Template Line'
    _order = 'sequence, component_id'
    
    template_id = fields.Many2one('kit.template', string='Template', required=True, ondelete='cascade')
    component_id = fields.Many2one('kit.component', string='Component', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    # Configuration
    default_enabled = fields.Boolean(string='Enabled by Default', default=True)
    is_mandatory = fields.Boolean(string='Mandatory', default=False)
    
    # Formulas
    quantity_formula = fields.Text(string='Quantity Formula')
    rate_formula = fields.Text(string='Rate Formula')
    
    # Related fields
    component_name = fields.Char(related='component_id.name', store=True)
    component_category = fields.Selection(related='component_id.category', store=True)
    current_rate = fields.Float(related='component_id.current_rate')

class KitTemplateParameter(models.Model):
    _name = 'kit.template.parameter'
    _description = 'Kit Template Parameter'
    _order = 'sequence, name'
    
    template_id = fields.Many2one('kit.template', string='Template', required=True, ondelete='cascade')
    name = fields.Char(string='Parameter Name', required=True)
    code = fields.Char(string='Parameter Code', required=True)
    parameter_type = fields.Selection([
        ('float', 'Number'),
        ('integer', 'Integer'),
        ('char', 'Text'),
        ('selection', 'Selection'),
        ('boolean', 'Yes/No')
    ], string='Type', required=True, default='float')
    
    sequence = fields.Integer(string='Sequence', default=10)
    required = fields.Boolean(string='Required', default=True)
    default_value = fields.Char(string='Default Value')
    description = fields.Text(string='Description')