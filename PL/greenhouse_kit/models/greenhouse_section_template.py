from odoo import models, fields, api


class GreenhouseSectionTemplate(models.Model):
    _name = 'greenhouse.section.template'
    _description = 'Greenhouse Section Template'
    _order = 'sequence, name'

    name = fields.Char(string='Section Name', required=True, help='e.g., Basic Dimensions')
    code = fields.Char(string='Section Code', required=True, help='Unique identifier for formulas')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    # Fields
    input_field_ids = fields.One2many(
        'greenhouse.field.template', 'section_id', 
        domain=[('field_type', '=', 'input')],
        string='Input Fields'
    )
    calculated_field_ids = fields.One2many(
        'greenhouse.field.template', 'section_id',
        domain=[('field_type', '=', 'calculated')], 
        string='Calculated Fields'
    )
    
    # Computed fields for easy access
    total_fields = fields.Integer(compute='_compute_field_counts', store=True)
    input_field_count = fields.Integer(compute='_compute_field_counts', store=True)
    calculated_field_count = fields.Integer(compute='_compute_field_counts', store=True)
    
    @api.depends('input_field_ids', 'calculated_field_ids')
    def _compute_field_counts(self):
        for record in self:
            record.input_field_count = len(record.input_field_ids)
            record.calculated_field_count = len(record.calculated_field_ids)
            record.total_fields = record.input_field_count + record.calculated_field_count
    
    _sql_constraints = [
        ('unique_code', 'unique(code)', 'Section code must be unique!')
    ]
