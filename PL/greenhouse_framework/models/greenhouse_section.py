# -*- coding: utf-8 -*-
from odoo import models, fields, api
import json

class GreenhouseSectionTemplate(models.Model):
    """Section templates like Frame, Truss, ASC"""
    _name = 'greenhouse.section.template'
    _description = 'Greenhouse Section Template'
    _order = 'sequence, name'
    
    name = fields.Char('Section Name', required=True)
    code = fields.Char('Code', required=True)
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean('Active', default=True)
    
    # Visual
    icon = fields.Char('Icon', default='fa-cube')
    color = fields.Integer('Color')
    
    # Configuration
    is_mandatory = fields.Boolean('Mandatory', help='Cannot be removed from project')
    requires_pipe = fields.Boolean('Requires Pipe Selection', default=True)
    
    # Input fields configuration (JSON)
    input_fields = fields.Text(
        'Input Field Definitions',
        help='JSON definition of input fields for this section'
    )
    
    # Calculation configuration (JSON)
    calculation_rules = fields.Text(
        'Calculation Rules',
        help='JSON definition of calculation formulas'
    )
    
    @api.model
    def get_input_fields(self):
        """Return input field definitions as list"""
        if self.input_fields:
            return json.loads(self.input_fields)
        return []
    
    @api.model
    def get_calculation_rules(self):
        """Return calculation rules as list"""
        if self.calculation_rules:
            return json.loads(self.calculation_rules)
        return []
