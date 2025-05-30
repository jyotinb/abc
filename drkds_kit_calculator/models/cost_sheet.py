# File: drkds_kit_calculator/models/cost_sheet.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import ast
import operator
import math
import re

class KitCostSheet(models.Model):
    _name = 'kit.cost.sheet'
    _description = 'Kit Cost Sheet'
    _order = 'create_date desc'
    
    name = fields.Char(string='Cost Sheet Number', required=True, default=_('New'))
    template_id = fields.Many2one('kit.template', string='Template', required=True)
    
    # Project Information
    project_name = fields.Char(string='Project Name')
    client_name = fields.Char(string='Client Name')
    site_location = fields.Char(string='Site Location')
    quotation_number = fields.Char(string='Quotation Number')
    
    # Parameters
    parameter_ids = fields.One2many('kit.cost.parameter', 'cost_sheet_id', string='Parameters')
    
    # Components
    component_ids = fields.One2many('kit.cost.line', 'cost_sheet_id', string='Components')
    
    # Calculations
    total_amount = fields.Float(string='Total Amount', compute='_compute_totals', store=True)
    enabled_amount = fields.Float(string='Enabled Amount', compute='_compute_totals', store=True)
    total_area = fields.Float(string='Total Area', compute='_compute_area')
    rate_per_sqm = fields.Float(string='Rate per m²', compute='_compute_rate_per_sqm')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('confirmed', 'Confirmed')
    ], string='Status', default='draft', tracking=True)
    
    notes = fields.Text(string='Notes')
    last_calculation = fields.Datetime(string='Last Calculation', readonly=True)
    
    # Keep auto_calculate field for backward compatibility (but not used)
    auto_calculate = fields.Boolean(string='Auto Calculate', default=False, 
                                   help="Auto calculation is disabled - use Calculate button instead")
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('kit.cost.sheet') or _('New')
        
        result = super().create(vals)
        if result.template_id:
            result._create_lines_from_template()
        return result
    
    def _create_lines_from_template(self):
        # Create parameter lines
        for param in self.template_id.parameter_ids:
            default_val = param.default_value or '0'
            self.env['kit.cost.parameter'].create({
                'cost_sheet_id': self.id,
                'parameter_id': param.id,
                'value_float': float(default_val) if param.data_type == 'float' else 0.0,
                'value_integer': int(default_val) if param.data_type == 'integer' else 0,
                'value_char': default_val if param.data_type == 'char' else '',
                'value_boolean': default_val.lower() in ('true', '1') if param.data_type == 'boolean' else False,
            })
        
        # Create component lines
        for comp in self.template_id.component_ids:
            self.env['kit.cost.line'].create({
                'cost_sheet_id': self.id,
                'component_id': comp.component_id.id,
                'template_line_id': comp.id,
                'is_enabled': comp.default_enabled,
                'is_mandatory': comp.is_mandatory,
                'sequence': comp.sequence,
                
                # Only values, not formulas (formulas come from template)
                'quantity': comp.qty_value,
                'rate': comp.rate_value or comp.component_id.current_rate,
                'length': comp.length_value,
            })
    
    @api.depends('component_ids.amount')
    def _compute_totals(self):
        for record in self:
            total = sum(line.amount for line in record.component_ids)
            enabled = sum(line.amount for line in record.component_ids if line.is_enabled)
            record.total_amount = total
            record.enabled_amount = enabled
    
    def _compute_area(self):
        for record in self:
            # Calculate area from parameters
            area = 0.0
            for param in record.parameter_ids:
                if 'area' in param.parameter_code.lower():
                    area = param.get_numeric_value()
                    break
            record.total_area = area
    
    @api.depends('enabled_amount', 'total_area')
    def _compute_rate_per_sqm(self):
        for record in self:
            if record.total_area > 0:
                record.rate_per_sqm = record.enabled_amount / record.total_area
            else:
                record.rate_per_sqm = 0.0
    
    def action_calculate(self):
        """Manual calculation - user clicks to calculate"""
        self.ensure_one()
        try:
            self._calculate_all_formulas()
            self.state = 'calculated'
            self.last_calculation = fields.Datetime.now()
            
            # Force UI refresh by returning a reload action
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
            
        except Exception as e:
            raise UserError(_('Calculation Error: %s') % str(e))
    
    def action_recalculate(self):
        """Manual recalculation action - recalculate with current values"""
        self.ensure_one()
        try:
            # Just recalculate with current values, don't reset
            self._calculate_all_formulas()
            self.last_calculation = fields.Datetime.now()
            
            # Force UI refresh by returning a reload action
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
            
        except Exception as e:
            raise UserError(_('Recalculation Error: %s') % str(e))
    
    def reset_to_template_values(self):
        """Reset all values to template defaults"""
        self.ensure_one()
        
        # Reset parameters to template defaults
        for param in self.parameter_ids:
            template_param = param.parameter_id
            if template_param:
                default_val = template_param.default_value or '0'
                try:
                    if param.data_type == 'float':
                        param.value_float = float(default_val)
                    elif param.data_type == 'integer':
                        param.value_integer = int(default_val)
                    elif param.data_type == 'char':
                        param.value_char = default_val
                    elif param.data_type == 'boolean':
                        param.value_boolean = default_val.lower() in ('true', '1')
                except (ValueError, TypeError):
                    # Handle invalid default values gracefully
                    if param.data_type == 'float':
                        param.value_float = 0.0
                    elif param.data_type == 'integer':
                        param.value_integer = 0
                    elif param.data_type == 'char':
                        param.value_char = ''
                    elif param.data_type == 'boolean':
                        param.value_boolean = False
        
        # Reset component lines to template defaults
        for line in self.component_ids:
            template_line = line.template_line_id
            if template_line:
                line.quantity = template_line.qty_value or 0.0
                line.rate = template_line.rate_value or line.component_id.current_rate
                line.length = template_line.length_value or 1.0

    def action_reset_and_recalculate(self):
        """Reset to template values then recalculate"""
        self.ensure_one()
        try:
            self.reset_to_template_values()
            self._calculate_all_formulas()
            self.last_calculation = fields.Datetime.now()
            
            # Force UI refresh by returning a reload action
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
            
        except Exception as e:
            raise UserError(_('Reset and Recalculation Error: %s') % str(e))
    
    def _sanitize_name(self, name):
        """Sanitize component name for use in formulas"""
        if not name:
            return "Component"
        # Replace spaces, hyphens, and other special characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = f"C_{sanitized}"
        return sanitized or "Component"
    
    def _calculate_all_formulas(self):
        """Calculate all formulas - read formulas from template"""
        # Build parameter context
        context = {'math': math}
        
        # First pass: get fixed and input parameters
        for param in self.parameter_ids:
            if param.parameter_type in ['fixed', 'input']:
                context[param.parameter_code] = param.get_numeric_value()
        
        # Second pass: calculate calculated parameters using template formulas
        calculated_params = self.parameter_ids.filtered(lambda p: p.parameter_type == 'calculated')
        
        # Calculate in iterations to handle dependencies
        max_iterations = 10
        for iteration in range(max_iterations):
            updated = False
            for param in calculated_params:
                # Get formula from template
                formula = param.parameter_id.formula
                if formula:
                    try:
                        value = self._safe_eval(formula, context)
                        if value is not None:
                            new_value = float(value)
                            # Check if this is actually a new/different value
                            current_value = param.get_numeric_value()
                            if abs(new_value - current_value) > 0.001:  # Avoid floating point precision issues
                                context[param.parameter_code] = new_value
                                # Update the parameter value
                                if param.data_type == 'float':
                                    param.value_float = new_value
                                elif param.data_type == 'integer':
                                    param.value_integer = int(new_value)
                                updated = True
                    except Exception as e:
                        # Skip if formula can't be evaluated yet
                        continue
            
            if not updated:
                break
        
        # Calculate component values using template formulas
        enabled_lines = self.component_ids.filtered(lambda l: l.is_enabled)
        
        # Calculate component formulas
        for line in enabled_lines:
            # Build component context fresh each time
            comp_context = context.copy()
            
            # Add OTHER component values to context (not current line)
            for other_line in enabled_lines:
                if other_line.id != line.id:
                    comp_name = self._sanitize_name(other_line.component_id.name)
                    comp_context[f"{comp_name}_Qty"] = other_line.quantity
                    comp_context[f"{comp_name}_Rate"] = other_line.rate
                    comp_context[f"{comp_name}_Length"] = other_line.length
            
            # Calculate quantity using template formula
            if line.qty_type == 'calculated' and line.template_line_id.qty_formula:
                try:
                    quantity = self._safe_eval(line.template_line_id.qty_formula, comp_context)
                    line.quantity = float(quantity) if quantity is not None else 0.0
                except Exception as e:
                    line.quantity = 0.0
            elif line.qty_type == 'fixed' and line.template_line_id:
                line.quantity = line.template_line_id.qty_value or 0.0
            
            # Calculate rate using template formula
            if line.rate_type == 'calculated' and line.template_line_id.rate_formula:
                try:
                    rate = self._safe_eval(line.template_line_id.rate_formula, comp_context)
                    line.rate = float(rate) if rate is not None else line.component_id.current_rate
                except Exception as e:
                    line.rate = line.component_id.current_rate
            elif line.rate_type == 'fixed' and line.template_line_id:
                line.rate = line.template_line_id.rate_value or line.component_id.current_rate
            
            # Calculate length using template formula
            if line.length_type == 'calculated' and line.template_line_id.length_formula:
                try:
                    length = self._safe_eval(line.template_line_id.length_formula, comp_context)
                    line.length = float(length) if length is not None else 1.0
                except Exception as e:
                    line.length = 1.0
            elif line.length_type == 'fixed' and line.template_line_id:
                line.length = line.template_line_id.length_value or 1.0
    
    def _safe_eval(self, expression, context):
        if not expression:
            return 0
        
        allowed_names = {
            "__builtins__": {"abs": abs, "min": min, "max": max, "round": round},
            "math": math,
        }
        allowed_names.update(context)
        
        try:
            node = ast.parse(expression, mode='eval')
            return eval(compile(node, '<string>', 'eval'), allowed_names)
        except Exception as e:
            raise UserError(_('Formula Error in "%s": %s') % (expression, str(e)))
    
    def action_confirm(self):
        self.ensure_one()
        if self.state != 'calculated':
            raise UserError(_('Please calculate the cost sheet first.'))
        self.state = 'confirmed'


class KitCostParameter(models.Model):
    _name = 'kit.cost.parameter'
    _description = 'Kit Cost Parameter'
    
    cost_sheet_id = fields.Many2one('kit.cost.sheet', string='Cost Sheet', required=True, ondelete='cascade')
    parameter_id = fields.Many2one('kit.template.parameter', string='Parameter', required=True)
    
    # Parameter details (from template)
    parameter_name = fields.Char(related='parameter_id.name', store=True)
    parameter_code = fields.Char(related='parameter_id.code', store=True)
    parameter_type = fields.Selection(related='parameter_id.parameter_type')
    data_type = fields.Selection(related='parameter_id.data_type')
    
    # Formula comes from template (read-only reference)
    formula = fields.Text(related='parameter_id.formula', string='Formula', readonly=True)
    
    # Only values are stored in cost sheet
    value_float = fields.Float(string='Float Value', digits=(12, 3))
    value_integer = fields.Integer(string='Integer Value')
    value_char = fields.Char(string='Text Value')
    value_boolean = fields.Boolean(string='Boolean Value')
    
    def get_numeric_value(self):
        if self.data_type == 'float':
            return self.value_float
        elif self.data_type == 'integer':
            return float(self.value_integer)
        elif self.data_type == 'boolean':
            return 1.0 if self.value_boolean else 0.0
        else:
            try:
                return float(self.value_char or '0')
            except:
                return 0.0
    
    def action_edit_parameter_formula(self):
        """Edit parameter formula in template (not cost sheet)"""
        return {
            'name': _('Edit Formula - %s') % self.parameter_name,
            'type': 'ir.actions.act_window',
            'res_model': 'kit.formula.builder.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.cost_sheet_id.template_id.id,
                'default_formula_type': 'parameter',
                'default_field_name': self.parameter_name,
                'default_formula': self.parameter_id.formula or '',
                'active_model': 'kit.template.parameter',
                'active_id': self.parameter_id.id,
                'target_field': 'formula'
            }
        }


class KitCostLine(models.Model):
    _name = 'kit.cost.line'
    _description = 'Kit Cost Line'
    _order = 'sequence, component_id'
    
    cost_sheet_id = fields.Many2one('kit.cost.sheet', string='Cost Sheet', required=True, ondelete='cascade')
    component_id = fields.Many2one('kit.component', string='Component', required=True)
    template_line_id = fields.Many2one('kit.template.line', string='Template Line')
    
    sequence = fields.Integer(string='Sequence', default=10)
    is_enabled = fields.Boolean(string='Enabled', default=True)
    is_mandatory = fields.Boolean(string='Mandatory', default=False)
    
    # Types come from template (read-only reference)
    qty_type = fields.Selection(related='template_line_id.qty_type', string='Quantity Type')
    rate_type = fields.Selection(related='template_line_id.rate_type', string='Rate Type')
    length_type = fields.Selection(related='template_line_id.length_type', string='Length Type')
    
    # Formulas come from template (read-only reference)
    qty_formula = fields.Text(related='template_line_id.qty_formula', string='Quantity Formula', readonly=True)
    rate_formula = fields.Text(related='template_line_id.rate_formula', string='Rate Formula', readonly=True)
    length_formula = fields.Text(related='template_line_id.length_formula', string='Length Formula', readonly=True)
    
    # Only calculated/input values are stored in cost sheet
    quantity = fields.Float(string='Quantity', digits=(12, 3), default=0.0)
    rate = fields.Float(string='Rate', digits=(12, 2), default=0.0)
    length = fields.Float(string='Length', default=1.0)
    
    amount = fields.Float(string='Amount', compute='_compute_amount', store=True)
    
    # Related fields
    component_name = fields.Char(related='component_id.name', store=True)
    component_category = fields.Selection(related='component_id.category')
    uom = fields.Selection(related='component_id.uom')
    
    @api.depends('quantity', 'rate', 'length', 'is_enabled')
    def _compute_amount(self):
        for line in self:
            if line.is_enabled:
                base_amount = line.quantity * line.rate
                if line.length and line.length > 0:
                    line.amount = base_amount * line.length
                else:
                    line.amount = base_amount
            else:
                line.amount = 0.0
    
    def toggle_component(self):
        self.ensure_one()
        if self.is_mandatory and self.is_enabled:
            raise ValidationError(_("Cannot disable mandatory component."))
        self.is_enabled = not self.is_enabled
    
    def action_edit_qty_formula(self):
        """Edit quantity formula in template (not cost sheet)"""
        return {
            'name': _('Edit Quantity Formula - %s') % self.component_name,
            'type': 'ir.actions.act_window',
            'res_model': 'kit.formula.builder.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.cost_sheet_id.template_id.id,
                'default_formula_type': 'quantity',
                'default_field_name': f'{self.component_name} - Quantity',
                'default_formula': self.template_line_id.qty_formula or '',
                'active_model': 'kit.template.line',
                'active_id': self.template_line_id.id,
                'target_field': 'qty_formula'
            }
        }
    
    def action_edit_rate_formula(self):
        """Edit rate formula in template (not cost sheet)"""
        return {
            'name': _('Edit Rate Formula - %s') % self.component_name,
            'type': 'ir.actions.act_window',
            'res_model': 'kit.formula.builder.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.cost_sheet_id.template_id.id,
                'default_formula_type': 'rate',
                'default_field_name': f'{self.component_name} - Rate',
                'default_formula': self.template_line_id.rate_formula or '',
                'active_model': 'kit.template.line',
                'active_id': self.template_line_id.id,
                'target_field': 'rate_formula'
            }
        }
    
    def action_edit_length_formula(self):
        """Edit length formula in template (not cost sheet)"""
        return {
            'name': _('Edit Length Formula - %s') % self.component_name,
            'type': 'ir.actions.act_window',
            'res_model': 'kit.formula.builder.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.cost_sheet_id.template_id.id,
                'default_formula_type': 'length',
                'default_field_name': f'{self.component_name} - Length',
                'default_formula': self.template_line_id.length_formula or '',
                'active_model': 'kit.template.line',
                'active_id': self.template_line_id.id,
                'target_field': 'length_formula'
            }
        }