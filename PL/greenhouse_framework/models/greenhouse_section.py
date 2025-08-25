# -*- coding: utf-8 -*-
from odoo import models, fields, api
import json
import logging

_logger = logging.getLogger(__name__)


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
    
    # Reverse relation to find which types use this section
    type_ids = fields.Many2many(
        'greenhouse.type',
        'greenhouse_type_section_rel',
        'section_id',
        'type_id',
        string='Used in Types',
        readonly=True
    )
    
    def get_input_fields(self):
        """Return input field definitions as list"""
        self.ensure_one()
        if self.input_fields:
            try:
                return json.loads(self.input_fields)
            except json.JSONDecodeError as e:
                _logger.error(f"Invalid JSON in input_fields for section {self.name}: {str(e)}")
                return []
        return []
    
    def get_calculation_rules(self):
        """Return calculation rules as list"""
        self.ensure_one()
        if self.calculation_rules:
            try:
                rules = json.loads(self.calculation_rules)
                # Ensure each rule has required fields
                for rule in rules:
                    if 'code' not in rule:
                        _logger.error(f"Rule missing 'code' in section {self.name}")
                        continue
                    if 'formula' not in rule:
                        rule['formula'] = '0'
                    if 'name' not in rule:
                        rule['name'] = rule['code'].replace('_', ' ').title()
                    if 'sequence' not in rule:
                        rule['sequence'] = 10
                return rules
            except json.JSONDecodeError as e:
                _logger.error(f"Invalid JSON in calculation_rules for section {self.name}: {str(e)}")
                return []
        return []
