# -*- coding: utf-8 -*-
from odoo import models, fields, api

class GreenhouseComponentResult(models.Model):
    """Store calculated component results - like Excel output cells"""
    _name = 'greenhouse.component.result'
    _description = 'Greenhouse Component Result'
    _order = 'section_id, sequence, name'
    
    project_id = fields.Many2one(
        'greenhouse.project',
        string='Project',
        required=True,
        ondelete='cascade'
    )
    
    section_id = fields.Many2one(
        'greenhouse.section.template',
        string='Section',
        required=True
    )
    
    # Component details
    name = fields.Char('Component Name', required=True)
    description = fields.Text('Description')
    sequence = fields.Integer('Sequence', default=10)
    
    # Quantities
    quantity = fields.Float('Quantity', default=0)
    length = fields.Float('Length (m)', default=0)
    total_length = fields.Float('Total Length (m)', compute='_compute_total_length', store=True)
    
    # Cost
    unit_cost = fields.Float('Unit Cost')
    total_cost = fields.Float('Total Cost', compute='_compute_total_cost', store=True)
    
    # Pipe selection (optional)
    requires_pipe = fields.Boolean('Requires Pipe', related='section_id.requires_pipe')
    pipe_type = fields.Char('Pipe Type')
    pipe_size = fields.Char('Pipe Size')
    pipe_selected = fields.Boolean('Pipe Selected', default=False)
    
    # Calculation metadata
    formula_used = fields.Text('Formula Used', help='For debugging')
    calculated_at = fields.Datetime('Calculated At', default=fields.Datetime.now)
    
    @api.depends('quantity', 'length')
    def _compute_total_length(self):
        for record in self:
            record.total_length = record.quantity * record.length
    
    @api.depends('quantity', 'unit_cost')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.quantity * record.unit_cost
