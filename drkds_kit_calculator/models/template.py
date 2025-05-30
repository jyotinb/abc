# File: drkds_kit_calculator/models/template.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import ast
import operator
import math
import re

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
    
    @api.model
    def get_available_fields_for_formula(self, template_id):
        """Get all available fields for formula building"""
        template = self.browse(template_id)
        fields_list = []
        
        # Add parameters
        for param in template.parameter_ids:
            fields_list.append({
                'name': param.code,
                'display_name': param.name,
                'type': 'parameter',
                'data_type': param.data_type,
                'id': param.id
            })
        
        # Add component fields
        for comp in template.component_ids:
            comp_name = comp.component_id.name.replace(' ', '_').replace('-', '_')
            fields_list.extend([
                {
                    'name': f"{comp_name}_Qty",
                    'display_name': f"{comp.component_id.name} - Quantity",
                    'type': 'component',
                    'data_type': 'float',
                    'id': f"{comp.id}_qty"
                },
                {
                    'name': f"{comp_name}_Rate", 
                    'display_name': f"{comp.component_id.name} - Rate",
                    'type': 'component',
                    'data_type': 'float',
                    'id': f"{comp.id}_rate"
                },
                {
                    'name': f"{comp_name}_Length",
                    'display_name': f"{comp.component_id.name} - Length", 
                    'type': 'component',
                    'data_type': 'float',
                    'id': f"{comp.id}_length"
                }
            ])
        
        return fields_list

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
    
    # Quantity Configuration
    qty_type = fields.Selection([
        ('fixed', 'Fixed'),
        ('input', 'Input'),
        ('calculated', 'Calculated')
    ], string='Quantity Type', default='input', required=True)
    qty_value = fields.Float(string='Quantity Value', default=1.0)
    qty_formula = fields.Text(string='Quantity Formula')
    
    # Rate Configuration  
    rate_type = fields.Selection([
        ('fixed', 'Fixed'),
        ('input', 'Input'), 
        ('calculated', 'Calculated')
    ], string='Rate Type', default='fixed', required=True)
    rate_value = fields.Float(string='Rate Value')
    rate_formula = fields.Text(string='Rate Formula')
    
    # Length Configuration
    length_type = fields.Selection([
        ('fixed', 'Fixed'),
        ('input', 'Input'),
        ('calculated', 'Calculated')
    ], string='Length Type', default='input', required=True)
    length_value = fields.Float(string='Length Value', default=1.0)
    length_formula = fields.Text(string='Length Formula')
    
    # Related fields
    component_name = fields.Char(related='component_id.name', store=True)
    component_category = fields.Selection(related='component_id.category', store=True)
    current_rate = fields.Float(related='component_id.current_rate')
    
    @api.onchange('component_id')
    def _onchange_component_id(self):
        if self.component_id:
            self.rate_value = self.component_id.current_rate
    
    @api.constrains('qty_formula', 'rate_formula', 'length_formula')
    def _check_formulas(self):
        for record in self:
            if record.qty_type == 'calculated' and not record.qty_formula:
                raise ValidationError(_("Quantity formula is required when type is 'Calculated'"))
            if record.rate_type == 'calculated' and not record.rate_formula:
                raise ValidationError(_("Rate formula is required when type is 'Calculated'"))
            if record.length_type == 'calculated' and not record.length_formula:
                raise ValidationError(_("Length formula is required when type is 'Calculated'"))
    
    def action_open_qty_formula_builder(self):
        """Open formula builder for quantity"""
        return {
            'name': _('Quantity Formula Builder - %s') % self.component_name,
            'type': 'ir.actions.act_window',
            'res_model': 'kit.formula.builder.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.template_id.id,
                'default_formula_type': 'quantity',
                'default_field_name': f'{self.component_name} - Quantity',
                'default_formula': self.qty_formula or '',
                'active_model': 'kit.template.line',
                'active_id': self.id,
                'target_field': 'qty_formula'
            }
        }
    
    def action_open_rate_formula_builder(self):
        """Open formula builder for rate"""
        return {
            'name': _('Rate Formula Builder - %s') % self.component_name,
            'type': 'ir.actions.act_window',
            'res_model': 'kit.formula.builder.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.template_id.id,
                'default_formula_type': 'rate',
                'default_field_name': f'{self.component_name} - Rate',
                'default_formula': self.rate_formula or '',
                'active_model': 'kit.template.line',
                'active_id': self.id,
                'target_field': 'rate_formula'
            }
        }
    
    def action_open_length_formula_builder(self):
        """Open formula builder for length"""
        return {
            'name': _('Length Formula Builder - %s') % self.component_name,
            'type': 'ir.actions.act_window',
            'res_model': 'kit.formula.builder.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.template_id.id,
                'default_formula_type': 'length',
                'default_field_name': f'{self.component_name} - Length',
                'default_formula': self.length_formula or '',
                'active_model': 'kit.template.line',
                'active_id': self.id,
                'target_field': 'length_formula'
            }
        }

class KitTemplateParameter(models.Model):
    _name = 'kit.template.parameter'
    _description = 'Kit Template Parameter'
    _order = 'sequence, name'
    
    template_id = fields.Many2one('kit.template', string='Template', required=True, ondelete='cascade')
    name = fields.Char(string='Parameter Name', required=True)
    code = fields.Char(string='Parameter Code', required=True)
    
    parameter_type = fields.Selection([
        ('fixed', 'Fixed'),
        ('input', 'Input'),
        ('calculated', 'Calculated')
    ], string='Parameter Type', required=True, default='input')
    
    data_type = fields.Selection([
        ('float', 'Number'),
        ('integer', 'Integer'),
        ('char', 'Text'),
        ('boolean', 'Yes/No')
    ], string='Data Type', required=True, default='float')
    
    sequence = fields.Integer(string='Sequence', default=10)
    required = fields.Boolean(string='Required', default=True)
    default_value = fields.Char(string='Default Value')
    formula = fields.Text(string='Formula', help="Formula for calculated parameters")
    description = fields.Text(string='Description')
    
    @api.constrains('parameter_type', 'formula')
    def _check_calculated_formula(self):
        for record in self:
            if record.parameter_type == 'calculated' and not record.formula:
                raise ValidationError(_("Formula is required for calculated parameters"))
    
    @api.constrains('code')
    def _check_code_unique(self):
        for record in self:
            domain = [('template_id', '=', record.template_id.id), ('code', '=', record.code), ('id', '!=', record.id)]
            if self.search_count(domain) > 0:
                raise ValidationError(_("Parameter code must be unique within the template"))
    
    @api.constrains('code')
    def _check_code_format(self):
        for record in self:
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', record.code):
                raise ValidationError(_("Parameter code must be a valid identifier (letters, numbers, underscore, no spaces)"))
    
    def action_open_formula_builder(self):
        """Open formula builder for parameter"""
        return {
            'name': _('Formula Builder - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'kit.formula.builder.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.template_id.id,
                'default_formula_type': 'parameter',
                'default_field_name': self.name,
                'default_formula': self.formula or '',
                'active_model': 'kit.template.parameter',
                'active_id': self.id,
                'target_field': 'formula'
            }
        }