# File: drkds_kit_calculator/wizard/formula_builder_wizard.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import ast
import math
import re

class KitFormulaBuilderWizard(models.TransientModel):
    _name = 'kit.formula.builder.wizard'
    _description = 'Formula Builder Wizard'
    
    # Context fields
    template_id = fields.Many2one('kit.template', string='Template')
    cost_sheet_id = fields.Many2one('kit.cost.sheet', string='Cost Sheet')
    
    # Formula configuration
    formula_type = fields.Selection([
        ('parameter', 'Parameter Formula'),
        ('quantity', 'Quantity Formula'),
        ('rate', 'Rate Formula'),
        ('length', 'Length Formula')
    ], string='Formula Type', required=True)
    
    field_name = fields.Char(string='Field Name', readonly=True)
    formula = fields.Text(string='Formula', required=True)
    
    # Available fields for formula building
    available_fields = fields.One2many('kit.formula.field', 'wizard_id', string='Available Fields')
    
    # Validation
    validation_result = fields.Text(string='Validation Result', readonly=True)
    
    # Target record information
    target_model = fields.Char(string='Target Model')
    target_field = fields.Char(string='Target Field')
    target_id = fields.Integer(string='Target ID')
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        # Get context information
        context = self.env.context
        if context.get('active_model') and context.get('active_id'):
            res['target_model'] = context.get('active_model')
            res['target_id'] = context.get('active_id')
            res['target_field'] = context.get('target_field', '')
            res['formula_type'] = context.get('formula_type', 'parameter')
            res['field_name'] = context.get('field_name', '')
            
            # Set template or cost sheet based on active model
            if context.get('active_model') == 'kit.template.parameter':
                param = self.env['kit.template.parameter'].browse(context.get('active_id'))
                if param.exists():
                    res['template_id'] = param.template_id.id
                    res['formula'] = param.formula or ''
            elif context.get('active_model') == 'kit.template.line':
                line = self.env['kit.template.line'].browse(context.get('active_id'))
                if line.exists():
                    res['template_id'] = line.template_id.id
                    if context.get('formula_type') == 'quantity':
                        res['formula'] = line.qty_formula or ''
                    elif context.get('formula_type') == 'rate':
                        res['formula'] = line.rate_formula or ''
                    elif context.get('formula_type') == 'length':
                        res['formula'] = line.length_formula or ''
            elif context.get('active_model') == 'kit.cost.parameter':
                param = self.env['kit.cost.parameter'].browse(context.get('active_id'))
                if param.exists():
                    res['cost_sheet_id'] = param.cost_sheet_id.id
                    res['template_id'] = param.cost_sheet_id.template_id.id
                    res['formula'] = param.formula or ''
            elif context.get('active_model') == 'kit.cost.line':
                line = self.env['kit.cost.line'].browse(context.get('active_id'))
                if line.exists():
                    res['cost_sheet_id'] = line.cost_sheet_id.id
                    res['template_id'] = line.cost_sheet_id.template_id.id
                    if context.get('formula_type') == 'quantity':
                        res['formula'] = line.qty_formula or ''
                    elif context.get('formula_type') == 'rate':
                        res['formula'] = line.rate_formula or ''
                    elif context.get('formula_type') == 'length':
                        res['formula'] = line.length_formula or ''
            
            # Also try to get template_id from context defaults
            if not res.get('template_id') and context.get('default_template_id'):
                res['template_id'] = context.get('default_template_id')
            
            # Get formula from context defaults if not set
            if not res.get('formula') and context.get('default_formula'):
                res['formula'] = context.get('default_formula')
        
        return res
    
    @api.model
    def create(self, vals):
        wizard = super().create(vals)
        wizard._populate_available_fields()
        return wizard
    
    def _populate_available_fields(self):
        """Populate available fields from template"""
        self.available_fields.unlink()
        
        if not self.template_id:
            return
            
        # Get fields from template
        try:
            fields_data = self.template_id.get_available_fields_for_formula(self.template_id.id)
            
            for field_data in fields_data:
                self.env['kit.formula.field'].create({
                    'wizard_id': self.id,
                    'name': field_data['name'],
                    'display_name': field_data['display_name'],
                    'type': field_data['type'],
                    'data_type': field_data['data_type'],
                    'field_id': str(field_data['id'])
                })
        except Exception as e:
            # Log error and continue
            import logging
            _logger = logging.getLogger(__name__)
            _logger.error(f"Error populating formula fields: {e}")
    
    def action_refresh_fields(self):
        """Manual refresh of available fields"""
        self._populate_available_fields()
        # Return the current wizard form to stay open
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'kit.formula.builder.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }
    
    def action_insert_field(self):
        """Insert selected field into formula"""
        field_line = self.env['kit.formula.field'].browse(self.env.context.get('active_id'))
        if field_line and field_line.wizard_id.id == self.id:
            current_formula = self.formula or ''
            # Add space before field name if formula is not empty
            separator = ' ' if current_formula and not current_formula.endswith(' ') else ''
            self.formula = current_formula + separator + field_line.name
        
        # Return the current wizard form to stay open
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'kit.formula.builder.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }
    
    def action_insert_operator(self):
        """Insert mathematical operator into formula"""
        operator = self.env.context.get('operator', '')
        if operator:
            current_formula = self.formula or ''
            # Add space around operators for readability
            if operator in ['+', '-', '*', '/', '**']:
                if current_formula and not current_formula.endswith(' '):
                    self.formula = current_formula + f' {operator} '
                else:
                    self.formula = current_formula + f'{operator} '
            else:
                self.formula = current_formula + operator
        
        # Return the current wizard form to stay open
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'kit.formula.builder.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }
    
    def action_validate_formula(self):
        """Validate the formula syntax and dependencies"""
        if not self.formula:
            self.validation_result = "Formula is empty"
            return
        
        try:
            # Check syntax by parsing
            ast.parse(self.formula, mode='eval')
            
            # Check if all referenced fields exist
            available_field_names = self.available_fields.mapped('name')
            
            # Extract field references from formula
            referenced_fields = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', self.formula)
            
            # Filter out math functions and operators
            math_functions = ['math', 'sqrt', 'abs', 'min', 'max', 'ceil', 'floor', 'sin', 'cos', 'tan']
            referenced_fields = [f for f in referenced_fields if f not in math_functions]
            
            missing_fields = []
            for field in referenced_fields:
                if field not in available_field_names:
                    missing_fields.append(field)
            
            if missing_fields:
                self.validation_result = f"Unknown fields: {', '.join(missing_fields)}"
            else:
                self.validation_result = "✓ Formula is valid"
                
        except SyntaxError as e:
            self.validation_result = f"Syntax error: {str(e)}"
        except Exception as e:
            self.validation_result = f"Error: {str(e)}"
        
        # Return the current wizard form to stay open
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'kit.formula.builder.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }
    
    def action_validate_and_save(self):
        """Validate and save formula if valid"""
        self.action_validate_formula()
        if self.validation_result.startswith("✓"):
            return self.action_save_formula()
        else:
            raise UserError(_("Please fix formula errors before saving:\n%s") % self.validation_result)
    
    def action_save_formula(self):
        """Save the formula to the target field"""
        if not self.formula:
            raise UserError(_("Formula cannot be empty"))
        
        # Validate formula before saving
        self.action_validate_formula()
        if not self.validation_result.startswith("✓"):
            raise UserError(_("Please fix formula errors before saving:\n%s") % self.validation_result)
        
        # Save to target record
        try:
            if self.target_model == 'kit.template.parameter':
                record = self.env['kit.template.parameter'].browse(self.target_id)
                if record.exists():
                    record.formula = self.formula
            elif self.target_model == 'kit.template.line':
                record = self.env['kit.template.line'].browse(self.target_id)
                if record.exists():
                    if self.formula_type == 'quantity':
                        record.qty_formula = self.formula
                    elif self.formula_type == 'rate':
                        record.rate_formula = self.formula
                    elif self.formula_type == 'length':
                        record.length_formula = self.formula
            elif self.target_model == 'kit.cost.parameter':
                record = self.env['kit.cost.parameter'].browse(self.target_id)
                if record.exists():
                    record.formula = self.formula
            elif self.target_model == 'kit.cost.line':
                record = self.env['kit.cost.line'].browse(self.target_id)
                if record.exists():
                    if self.formula_type == 'quantity':
                        record.qty_formula = self.formula
                    elif self.formula_type == 'rate':
                        record.rate_formula = self.formula
                    elif self.formula_type == 'length':
                        record.length_formula = self.formula
                        
            # Show success message and close wizard
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Formula saved successfully!'),
                    'type': 'success',
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        except Exception as e:
            raise UserError(_("Error saving formula: %s") % str(e))

class KitFormulaField(models.TransientModel):
    _name = 'kit.formula.field'
    _description = 'Available Field for Formula Building'
    
    wizard_id = fields.Many2one('kit.formula.builder.wizard', string='Wizard', ondelete='cascade')
    name = fields.Char(string='Field Name', required=True)
    display_name = fields.Char(string='Display Name', required=True)
    type = fields.Selection([
        ('parameter', 'Parameter'),
        ('component', 'Component')
    ], string='Type', required=True)
    data_type = fields.Selection([
        ('float', 'Number'),
        ('integer', 'Integer'),
        ('char', 'Text'),
        ('boolean', 'Boolean')
    ], string='Data Type', required=True)
    field_id = fields.Char(string='Field ID')
    
    def action_insert_field(self):
        """Insert this field into the formula"""
        if self.wizard_id:
            current_formula = self.wizard_id.formula or ''
            # Add space before field name if formula is not empty
            separator = ' ' if current_formula and not current_formula.endswith(' ') else ''
            self.wizard_id.formula = current_formula + separator + self.name
        
        # Return the current wizard form to stay open
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'kit.formula.builder.wizard',
            'res_id': self.wizard_id.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }