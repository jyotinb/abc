# File: drkds_kit_calculator/models/cost_sheet.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import ast
import operator
import math
import re
import logging

_logger = logging.getLogger(__name__)

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
            _logger.error(f"Calculation Error in cost sheet {self.id}: {e}", exc_info=True)
            raise UserError(_('Calculation Error: %s') % str(e))
    
    def action_recalculate(self):
        """Manual recalculation action - recalculate with current values"""
        self.ensure_one()
        
        # Use database transaction for better reliability
        with self.env.cr.savepoint():
            try:
                _logger.info(f"Starting recalculation for cost sheet {self.id}")
                
                # Force recalculation with current values
                self._calculate_all_formulas()
                self.last_calculation = fields.Datetime.now()
                
                # Explicit commit within savepoint
                # No flush needed - write() handles persistence
                
                _logger.info(f"Recalculation completed successfully for cost sheet {self.id}")
                
                # Force UI refresh by returning a reload action
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
                
            except Exception as e:
                _logger.error(f"Recalculation Error in cost sheet {self.id}: {e}", exc_info=True)
                # Rollback happens automatically with savepoint
                raise UserError(_('Recalculation Error: %s') % str(e))
    
    def reset_to_template_values(self):
        """Reset all values to template defaults"""
        self.ensure_one()
        
        _logger.info(f"Resetting cost sheet {self.id} to template values")
        
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
        
        # Database persistence handled by Odoo automatically

    def action_reset_and_recalculate(self):
        """Reset to template values then recalculate"""
        self.ensure_one()
        
        with self.env.cr.savepoint():
            try:
                _logger.info(f"Reset and recalculation started for cost sheet {self.id}")
                
                self.reset_to_template_values()
                self._calculate_all_formulas()
                self.last_calculation = fields.Datetime.now()
                
                # Explicit commit within savepoint
                # No flush needed - write() handles persistence
                
                _logger.info(f"Reset and recalculation completed for cost sheet {self.id}")
                
                # Force UI refresh by returning a reload action
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
                
            except Exception as e:
                _logger.error(f"Reset and Recalculation Error in cost sheet {self.id}: {e}", exc_info=True)
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
        """Calculate all formulas - use actual calculated values, not cached fields"""
        _logger.info(f"=== CALCULATION START for cost sheet {self.id} ===")
        
        # Step 1: Calculate parameters first
        context = {'math': math}
        
        # Get current parameter values
        for param in self.parameter_ids:
            if param.parameter_type in ['fixed', 'input']:
                context[param.parameter_code] = param.get_numeric_value()
        
        # Calculate parameters with dependency resolution
        calculated_params = self.parameter_ids.filtered(lambda p: p.parameter_type == 'calculated')
        for iteration in range(10):
            updated = False
            for param in calculated_params:
                if param.parameter_id.formula:
                    try:
                        old_value = param.get_numeric_value()
                        new_value = float(self._safe_eval(param.parameter_id.formula, context))
                        if abs(new_value - old_value) > 0.001:
                            if param.data_type == 'float':
                                param.value_float = new_value
                            elif param.data_type == 'integer':
                                param.value_integer = int(new_value)
                            context[param.parameter_code] = new_value
                            updated = True
                    except:
                        pass
            if not updated:
                break
        
        # Step 2: Calculate components - track ACTUAL calculated values
        enabled_lines = self.component_ids.filtered(lambda l: l.is_enabled).sorted('sequence')
        
        # Dictionary to track ACTUAL calculated values (not cached fields)
        actual_values = {}
        
        # Initialize with current field values
        for line in enabled_lines:
            comp_name = self._sanitize_name(line.component_id.name)
            actual_values[comp_name] = {
                'quantity': line.quantity,
                'rate': line.rate,
                'length': line.length
            }
        
        # Multiple iterations to resolve dependencies
        for iteration in range(5):
            updated = False
            _logger.debug(f"Component iteration {iteration + 1}")
            
            for line in enabled_lines:
                comp_name = self._sanitize_name(line.component_id.name)
                
                # Build context with parameters + ACTUAL calculated values + CALCULATED PARAMETERS
                comp_context = context.copy()
                
                # *** FIX: ADD ALL CALCULATED PARAMETERS TO COMPONENT CONTEXT ***
                for param in self.parameter_ids:
                    comp_context[param.parameter_code] = param.get_numeric_value()
                
                # Add component values
                for other_name, values in actual_values.items():
                    comp_context[f"{other_name}_Qty"] = values['quantity']
                    comp_context[f"{other_name}_Rate"] = values['rate']
                    comp_context[f"{other_name}_Length"] = values['length']
                
                old_qty, old_rate, old_length = line.quantity, line.rate, line.length
                
                # Calculate quantity
                if line.qty_type == 'calculated' and line.template_line_id and line.template_line_id.qty_formula:
                    try:
                        new_qty = float(self._safe_eval(line.template_line_id.qty_formula, comp_context))
                        line.quantity = new_qty
                        actual_values[comp_name]['quantity'] = new_qty  # Update ACTUAL value immediately
                        _logger.debug(f"{line.component_name} qty: {line.template_line_id.qty_formula} = {new_qty}")
                    except Exception as e:
                        _logger.warning(f"Quantity calc failed for {line.component_name}: {e}")
                        line.quantity = 0.0
                        actual_values[comp_name]['quantity'] = 0.0
                elif line.qty_type == 'fixed' and line.template_line_id:
                    new_qty = line.template_line_id.qty_value or 0.0
                    line.quantity = new_qty
                    actual_values[comp_name]['quantity'] = new_qty
                # For input type, keep current value and update actual_values
                else:
                    actual_values[comp_name]['quantity'] = line.quantity
                
                # Calculate rate
                if line.rate_type == 'calculated' and line.template_line_id and line.template_line_id.rate_formula:
                    try:
                        new_rate = float(self._safe_eval(line.template_line_id.rate_formula, comp_context))
                        line.rate = new_rate
                        actual_values[comp_name]['rate'] = new_rate  # Update ACTUAL value immediately
                        _logger.debug(f"{line.component_name} rate: {line.template_line_id.rate_formula} = {new_rate}")
                    except Exception as e:
                        _logger.warning(f"Rate calc failed for {line.component_name}: {e}")
                        line.rate = line.component_id.current_rate
                        actual_values[comp_name]['rate'] = line.rate
                elif line.rate_type == 'fixed' and line.template_line_id:
                    new_rate = line.template_line_id.rate_value or line.component_id.current_rate
                    line.rate = new_rate
                    actual_values[comp_name]['rate'] = new_rate
                else:
                    actual_values[comp_name]['rate'] = line.rate
                
                # Calculate length
                if line.length_type == 'calculated' and line.template_line_id and line.template_line_id.length_formula:
                    try:
                        new_length = float(self._safe_eval(line.template_line_id.length_formula, comp_context))
                        line.length = new_length
                        actual_values[comp_name]['length'] = new_length  # Update ACTUAL value immediately
                        _logger.debug(f"{line.component_name} length: {line.template_line_id.length_formula} = {new_length}")
                    except Exception as e:
                        _logger.warning(f"Length calc failed for {line.component_name}: {e}")
                        line.length = 1.0
                        actual_values[comp_name]['length'] = 1.0
                elif line.length_type == 'fixed' and line.template_line_id:
                    new_length = line.template_line_id.length_value or 1.0
                    line.length = new_length
                    actual_values[comp_name]['length'] = new_length
                else:
                    actual_values[comp_name]['length'] = line.length
                
                # Check if anything changed
                if (abs(line.quantity - old_qty) > 0.001 or 
                    abs(line.rate - old_rate) > 0.01 or 
                    abs(line.length - old_length) > 0.001):
                    updated = True
                    _logger.debug(f"Updated {line.component_name}: qty={old_qty}->{line.quantity}")
            
            # If nothing changed, we're done
            if not updated:
                _logger.debug(f"Components converged after {iteration + 1} iterations")
                break
        
        _logger.info(f"=== CALCULATION COMPLETED ===")
        
        # Log final values for debugging
        for line in enabled_lines:
            comp_name = self._sanitize_name(line.component_id.name)
            _logger.debug(f"Final {line.component_name}: qty={line.quantity}, rate={line.rate}, length={line.length}")
            _logger.debug(f"Actual values: {actual_values[comp_name]}")
    
    def _reset_to_clean_state(self):
        """Reset ONLY calculated values to template defaults - preserve user inputs"""
        _logger.debug("Resetting ONLY calculated values to clean template state")
        
        for line in self.component_ids:
            if line.template_line_id:
                # Reset ONLY calculated fields to template defaults
                # Keep input/fixed values as they are (user may have changed them)
                
                # Reset quantity only if it's calculated type
                if line.qty_type == 'calculated':
                    line.quantity = line.template_line_id.qty_value or 1.0
                # For input/fixed qty_type: keep current user value
                
                # Reset rate only if it's calculated type  
                if line.rate_type == 'calculated':
                    line.rate = line.template_line_id.rate_value or line.component_id.current_rate
                # For input/fixed rate_type: keep current user value
                
                # Reset length only if it's calculated type
                if line.length_type == 'calculated':
                    line.length = line.template_line_id.length_value or 1.0
                # For input/fixed length_type: keep current user value
                
                _logger.debug(f"Reset {line.component_name}: qty_type={line.qty_type}, rate_type={line.rate_type}, length_type={line.length_type}")
        
        # Reset ONLY calculated parameters to defaults (preserve user input parameters)
        for param in self.parameter_ids.filtered(lambda p: p.parameter_type == 'calculated'):
            if param.parameter_id.default_value:
                try:
                    default_val = param.parameter_id.default_value
                    if param.data_type == 'float':
                        param.value_float = float(default_val)
                    elif param.data_type == 'integer':
                        param.value_integer = int(default_val)
                    elif param.data_type == 'char':
                        param.value_char = default_val
                    elif param.data_type == 'boolean':
                        param.value_boolean = default_val.lower() in ('true', '1')
                        
                    _logger.debug(f"Reset calculated parameter {param.parameter_code} to {default_val}")
                except:
                    # If default value is invalid, set to zero/empty
                    if param.data_type == 'float':
                        param.value_float = 0.0
                    elif param.data_type == 'integer':
                        param.value_integer = 0
                    elif param.data_type == 'char':
                        param.value_char = ''
                    elif param.data_type == 'boolean':
                        param.value_boolean = False
    
    def _build_fresh_parameter_context(self):
        """Build fresh parameter context from current database state"""
        context = {'math': math}
        
        # Re-read parameters from database
        self.parameter_ids.read()
        
        # First pass: get fixed and input parameters
        for param in self.parameter_ids:
            if param.parameter_type in ['fixed', 'input']:
                value = param.get_numeric_value()
                context[param.parameter_code] = value
                _logger.debug(f"Parameter {param.parameter_code}: {value} (type: {param.parameter_type})")
        
        return context
    
    def _calculate_parameters(self, context):
        """Calculate calculated parameters with dependency resolution"""
        calculated_params = self.parameter_ids.filtered(lambda p: p.parameter_type == 'calculated')
        
        if not calculated_params:
            _logger.debug("No calculated parameters to process")
            return
        
        _logger.info(f"Calculating {len(calculated_params)} calculated parameters")
        
        # Calculate in iterations to handle dependencies
        max_iterations = 10
        for iteration in range(max_iterations):
            updated = False
            _logger.debug(f"Parameter iteration {iteration + 1}")
            
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
                                
                                # Update the parameter value using write() for better persistence
                                if param.data_type == 'float':
                                    param.write({'value_float': new_value})
                                elif param.data_type == 'integer':
                                    param.write({'value_integer': int(new_value)})
                                
                                updated = True
                                _logger.debug(f"Updated parameter {param.parameter_code}: {current_value} -> {new_value}")
                    except Exception as e:
                        _logger.warning(f"Failed to calculate parameter {param.parameter_code} with formula '{formula}': {e}")
                        continue
            
            if not updated:
                _logger.debug(f"Parameter calculation converged after {iteration + 1} iterations")
                break
        else:
            _logger.warning(f"Parameter calculation did not converge after {max_iterations} iterations")
    
    def _calculate_components(self, context):
        """Calculate component values using template formulas with dependency resolution"""
        # Re-read component state and get enabled lines
        self.component_ids.read()
        enabled_lines = self.component_ids.filtered(lambda l: l.is_enabled).sorted('sequence')
        
        if not enabled_lines:
            _logger.debug("No enabled components to calculate")
            return
        
        _logger.info(f"Calculating {len(enabled_lines)} enabled components")
        
        # Use multiple iterations to resolve component dependencies
        max_iterations = 5
        for iteration in range(max_iterations):
            updated = False
            _logger.debug(f"Component calculation iteration {iteration + 1}")
            
            # Calculate component formulas in sequence order
            for line in enabled_lines:
                _logger.debug(f"Processing component {line.sequence}: {line.component_name}")
                
                # Build component context fresh for each component with CURRENT values
                comp_context = context.copy()
                
                # Add ALL OTHER component values to context (with fresh values)
                for other_line in enabled_lines:
                    if other_line.id != line.id:
                        # Re-read to get latest calculated values
                        other_line.read(['quantity', 'rate', 'length'])
                        comp_name = self._sanitize_name(other_line.component_id.name)
                        comp_context[f"{comp_name}_Qty"] = other_line.quantity
                        comp_context[f"{comp_name}_Rate"] = other_line.rate
                        comp_context[f"{comp_name}_Length"] = other_line.length
                        _logger.debug(f"Added to context: {comp_name}_Qty={other_line.quantity}")
                
                # Store original values for comparison
                original_quantity = line.quantity
                original_rate = line.rate
                original_length = line.length
                
                # Calculate quantity using template formula
                new_quantity = line.quantity
                if line.qty_type == 'calculated' and line.template_line_id and line.template_line_id.qty_formula:
                    try:
                        quantity = self._safe_eval(line.template_line_id.qty_formula, comp_context)
                        new_quantity = float(quantity) if quantity is not None else 0.0
                        _logger.debug(f"Calculated quantity for {line.component_name}: {line.template_line_id.qty_formula} = {new_quantity}")
                    except Exception as e:
                        _logger.warning(f"Failed to calculate quantity for {line.component_name}: {e}")
                        new_quantity = 0.0
                elif line.qty_type == 'fixed' and line.template_line_id:
                    new_quantity = line.template_line_id.qty_value or 0.0
                
                # Calculate rate using template formula
                new_rate = line.rate
                if line.rate_type == 'calculated' and line.template_line_id and line.template_line_id.rate_formula:
                    try:
                        rate = self._safe_eval(line.template_line_id.rate_formula, comp_context)
                        new_rate = float(rate) if rate is not None else line.component_id.current_rate
                        _logger.debug(f"Calculated rate for {line.component_name}: {line.template_line_id.rate_formula} = {new_rate}")
                    except Exception as e:
                        _logger.warning(f"Failed to calculate rate for {line.component_name}: {e}")
                        new_rate = line.component_id.current_rate
                elif line.rate_type == 'fixed' and line.template_line_id:
                    new_rate = line.template_line_id.rate_value or line.component_id.current_rate
                
                # Calculate length using template formula
                new_length = line.length
                if line.length_type == 'calculated' and line.template_line_id and line.template_line_id.length_formula:
                    try:
                        length = self._safe_eval(line.template_line_id.length_formula, comp_context)
                        new_length = float(length) if length is not None else 1.0
                        _logger.debug(f"Calculated length for {line.component_name}: {line.template_line_id.length_formula} = {new_length}")
                    except Exception as e:
                        _logger.warning(f"Failed to calculate length for {line.component_name}: {e}")
                        new_length = 1.0
                elif line.length_type == 'fixed' and line.template_line_id:
                    new_length = line.template_line_id.length_value or 1.0
                
                # Check if values actually changed (avoid unnecessary updates)
                if (abs(new_quantity - original_quantity) > 0.001 or 
                    abs(new_rate - original_rate) > 0.01 or 
                    abs(new_length - original_length) > 0.001):
                    
                    # Update component values immediately
                    line.write({
                        'quantity': new_quantity,
                        'rate': new_rate,
                        'length': new_length,
                    })
                    
                    # Force immediate database flush
                    self.env.flush_all()
                    
                    updated = True
                    _logger.debug(f"Updated {line.component_name}: qty={original_quantity}->{new_quantity}, rate={original_rate}->{new_rate}, length={original_length}->{new_length}")
            
            # If no values changed in this iteration, we're done
            if not updated:
                _logger.debug(f"Component calculation converged after {iteration + 1} iterations")
                break
                
            # Small delay and cache clear between iterations
            self.env.invalidate_all()
            
        else:
            _logger.warning(f"Component calculation did not converge after {max_iterations} iterations")
    
    def _safe_eval(self, expression, context):
        """Safely evaluate mathematical expressions"""
        if not expression:
            return 0
        
        allowed_names = {
            "__builtins__": {"abs": abs, "min": min, "max": max, "round": round},
            "math": math,
        }
        allowed_names.update(context)
        
        try:
            node = ast.parse(expression, mode='eval')
            result = eval(compile(node, '<string>', 'eval'), allowed_names)
            _logger.debug(f"Formula '{expression}' evaluated to: {result}")
            return result
        except Exception as e:
            _logger.error(f"Formula Error in '{expression}': {e}")
            raise UserError(_('Formula Error in "%s": %s') % (expression, str(e)))
    
    def action_confirm(self):
        self.ensure_one()
        if self.state != 'calculated':
            raise UserError(_('Please calculate the cost sheet first.'))
        self.state = 'confirmed'
    
    def debug_fundamentals(self):
        """Debug the fundamental issues we might be missing"""
        _logger.info("=== FUNDAMENTAL DEBUG START ===")
        
        # Test 1: Basic formula evaluation
        _logger.info("--- TEST 1: Basic Formula Evaluation ---")
        context = {'length_8m': 48, 'safety_factor': 1.1, 'math': math}
        test_formulas = [
            "length_8m * 2",
            "length_8m * safety_factor", 
            "48 * 1.1",
            "math.ceil(10.5)"
        ]
        
        for formula in test_formulas:
            try:
                result = self._safe_eval(formula, context)
                _logger.info(f"✅ {formula} = {result}")
            except Exception as e:
                _logger.error(f"❌ {formula} failed: {e}")
        
        # Test 2: Parameter data
        _logger.info("--- TEST 2: Parameter Data ---")
        for param in self.parameter_ids:
            _logger.info(f"Parameter: {param.parameter_name}")
            _logger.info(f"  Code: {param.parameter_code}")
            _logger.info(f"  Type: {param.parameter_type}")
            _logger.info(f"  Current Value: {param.get_numeric_value()}")
            _logger.info(f"  Template Formula: '{param.parameter_id.formula or 'EMPTY'}'")
        
        # Test 3: Component template data
        _logger.info("--- TEST 3: Component Template Data ---")
        for line in self.component_ids:
            _logger.info(f"\nComponent: {line.component_name}")
            _logger.info(f"  Component ID: {line.component_id.id}")
            _logger.info(f"  Template Line ID: {line.template_line_id.id if line.template_line_id else 'MISSING'}")
            
            if line.template_line_id:
                _logger.info(f"  qty_type: {line.qty_type}")
                _logger.info(f"  qty_formula: '{line.template_line_id.qty_formula or 'EMPTY'}'")
                _logger.info(f"  rate_type: {line.rate_type}")
                _logger.info(f"  rate_formula: '{line.template_line_id.rate_formula or 'EMPTY'}'")
                _logger.info(f"  length_type: {line.length_type}")
                _logger.info(f"  length_formula: '{line.template_line_id.length_formula or 'EMPTY'}'")
            else:
                _logger.error(f"  ❌ NO TEMPLATE LINE LINKED!")
            
            _logger.info(f"  Current Values: qty={line.quantity}, rate={line.rate}, length={line.length}")
        
        # Test 4: Component name sanitization
        _logger.info("--- TEST 4: Component Name Sanitization ---")
        for line in self.component_ids:
            original_name = line.component_id.name
            sanitized = self._sanitize_name(original_name)
            _logger.info(f"'{original_name}' → '{sanitized}'")
            _logger.info(f"  Context keys: {sanitized}_Qty, {sanitized}_Rate, {sanitized}_Length")
        
        # Test 5: Check if formulas reference correct field names
        _logger.info("--- TEST 5: Formula Field Name Check ---")
        all_component_names = [self._sanitize_name(line.component_id.name) for line in self.component_ids]
        
        for line in self.component_ids:
            if line.template_line_id and line.template_line_id.qty_formula:
                formula = line.template_line_id.qty_formula
                _logger.info(f"Formula: '{formula}'")
                
                # Check if formula references any component names
                for comp_name in all_component_names:
                    if comp_name in formula:
                        _logger.info(f"  ✅ References: {comp_name}")
                
                # Look for unknown references
                import re
                refs = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', formula)
                unknown_refs = []
                for ref in refs:
                    if ref not in ['math', 'abs', 'min', 'max', 'round', 'ceil', 'floor']:
                        # Check if it's a parameter
                        param_codes = [p.parameter_code for p in self.parameter_ids]
                        if ref not in param_codes and not any(ref.startswith(cn) for cn in all_component_names):
                            unknown_refs.append(ref)
                
                if unknown_refs:
                    _logger.warning(f"  ⚠️ Unknown references: {unknown_refs}")
        
        # Test 6: Actual calculation attempt
        _logger.info("--- TEST 6: Single Component Calculation Test ---")
        context = {'math': math}
        
        # Add parameters to context
        for param in self.parameter_ids:
            if param.parameter_type in ['fixed', 'input']:
                context[param.parameter_code] = param.get_numeric_value()
        
        # Add current component values to context
        for line in self.component_ids:
            comp_name = self._sanitize_name(line.component_id.name)
            context[f"{comp_name}_Qty"] = line.quantity
            context[f"{comp_name}_Rate"] = line.rate
            context[f"{comp_name}_Length"] = line.length
        
        _logger.info(f"Context keys: {list(context.keys())}")
        
        # Try to calculate first component with calculated qty
        for line in self.component_ids:
            if line.qty_type == 'calculated' and line.template_line_id and line.template_line_id.qty_formula:
                formula = line.template_line_id.qty_formula
                _logger.info(f"\nTesting calculation for: {line.component_name}")
                _logger.info(f"Formula: {formula}")
                _logger.info(f"Current quantity: {line.quantity}")
                
                try:
                    result = self._safe_eval(formula, context)
                    _logger.info(f"✅ Calculation result: {result}")
                    _logger.info(f"Difference from current: {abs(float(result) - line.quantity)}")
                except Exception as e:
                    _logger.error(f"❌ Calculation failed: {e}")
                
                break  # Test only first one
        
        _logger.info("=== FUNDAMENTAL DEBUG END ===")
        return True


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
        """Get numeric value for calculations"""
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
        """Toggle component enabled/disabled state"""
        self.ensure_one()
        if self.is_mandatory and self.is_enabled:
            raise ValidationError(_("Cannot disable mandatory component."))
        
        old_state = self.is_enabled
        self.is_enabled = not self.is_enabled
        
        # Force database flush for immediate persistence
        self.env.flush_all()
        
        _logger.info(f"Toggled component {self.component_name}: {old_state} -> {self.is_enabled}")
    
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