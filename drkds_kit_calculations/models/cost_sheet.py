from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import ast
import operator
import math

class CostSheet(models.Model):
    _name = 'drkds.cost.sheet'
    _description = 'Cost Sheet Calculation'
    _order = 'create_date desc'
    _rec_name = 'name'
    
    # Basic Information
    name = fields.Char(string='Cost Sheet Number', required=True, 
                      default=lambda self: _('New'))
    template_id = fields.Many2one('drkds.cost.template', string='Template', 
                                required=True)
    
    # Project Information
    client_id = fields.Many2one('res.partner', string='Client', required=True)
    quotation_number = fields.Char(string='Quotation Number')
    site_location = fields.Char(string='Site Location')
    project_name = fields.Char(string='Project Name')
    installation_position = fields.Selection([
        ('inside', 'Inside'),
        ('outside', 'Outside')
    ], string='Installation Position', default='inside')
    
    # Parameters
    parameter_line_ids = fields.One2many('drkds.cost.parameter', 'cost_sheet_id',
                                       string='Parameters')
    
    # BOM Lines
    bom_line_ids = fields.One2many('drkds.cost.bom.line', 'cost_sheet_id',
                                 string='Bill of Materials')
    
    # Totals
    total_amount = fields.Float(string='Total Amount', compute='_compute_totals', store=True)
    total_area = fields.Float(string='Total Area', compute='_compute_area')
    rate_per_sqm = fields.Float(string='Rate per SQM', compute='_compute_rate_per_sqm', store=True)
    enabled_components_total = fields.Float(string='Enabled Components Total', 
                                          compute='_compute_totals', store=True)
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Dates
    calculation_date = fields.Datetime(string='Calculation Date')
    confirmation_date = fields.Datetime(string='Confirmation Date')
    
    # Notes
    notes = fields.Text(string='Notes')
    internal_notes = fields.Text(string='Internal Notes')
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('drkds.cost.sheet') or _('New')
        
        result = super().create(vals)
        
        # Create parameter lines from template
        if result.template_id:
            result._create_parameter_lines()
            result._create_bom_lines()
        
        # Log creation
        self.env['drkds.change.log'].log_change(
            action_type='create',
            object_model=self._name,
            object_id=result.id,
            object_name=result.name,
            description=f'Cost sheet "{result.name}" created for client "{result.client_id.name}"'
        )
        
        return result
    
    def _create_parameter_lines(self):
        """Create parameter lines from template"""
        for param in self.template_id.parameter_line_ids:
            vals = {
                'cost_sheet_id': self.id,
                'parameter_id': param.id,
            }
            # Set default values based on parameter type
            if param.default_value:
                if param.parameter_type == 'float':
                    try:
                        vals['value_float'] = float(param.default_value)
                    except:
                        pass
                elif param.parameter_type == 'integer':
                    try:
                        vals['value_integer'] = int(param.default_value)
                    except:
                        pass
                elif param.parameter_type == 'char':
                    vals['value_char'] = param.default_value
                elif param.parameter_type == 'selection':
                    vals['value_selection'] = param.default_value
                elif param.parameter_type == 'boolean':
                    vals['value_boolean'] = param.default_value.lower() in ('true', '1', 'yes')
            
            self.env['drkds.cost.parameter'].create(vals)
    
    def _create_bom_lines(self):
        """Create BOM lines from template"""
        for comp in self.template_id.component_line_ids:
            vals = {
                'cost_sheet_id': self.id,
                'component_id': comp.component_id.id,
                'template_component_id': comp.id,
                'is_enabled': comp.default_enabled,
                'is_mandatory': comp.is_mandatory,
                'sequence': comp.sequence,
                'quantity': 0.0,
                'rate': comp.component_id.current_rate,
            }
            self.env['drkds.cost.bom.line'].create(vals)
    
    @api.depends('bom_line_ids.amount')
    def _compute_totals(self):
        for record in self:
            total = sum(line.amount for line in record.bom_line_ids)
            enabled_total = sum(line.amount for line in record.bom_line_ids if line.is_enabled)
            record.total_amount = total
            record.enabled_components_total = enabled_total
    
    def _compute_area(self):
        """Calculate total area from parameters"""
        for record in self:
            area = 0.0
            # Look for area parameter
            area_param = record.parameter_line_ids.filtered(
                lambda p: 'area' in p.parameter_code.lower()
            )
            if area_param:
                area = area_param[0].get_numeric_value()
            record.total_area = area
    
    @api.depends('enabled_components_total', 'total_area')
    def _compute_rate_per_sqm(self):
        for record in self:
            if record.total_area > 0:
                record.rate_per_sqm = record.enabled_components_total / record.total_area
            else:
                record.rate_per_sqm = 0.0
    
    def action_calculate(self):
        """Trigger calculation of all formulas"""
        self.ensure_one()
        try:
            self._calculate_all_formulas()
            self.state = 'calculated'
            self.calculation_date = fields.Datetime.now()
            
            # Log calculation
            self.env['drkds.change.log'].log_change(
                action_type='calculation',
                object_model=self._name,
                object_id=self.id,
                object_name=self.name,
                description=f'Cost sheet "{self.name}" calculated. Total: {self.enabled_components_total}'
            )
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Cost sheet calculated successfully!'),
                    'type': 'success',
                }
            }
        except Exception as e:
            raise UserError(_('Calculation Error: %s') % str(e))
    
    def action_confirm(self):
        """Confirm the cost sheet"""
        self.ensure_one()
        if self.state != 'calculated':
            raise UserError(_('Please calculate the cost sheet first.'))
        
        self.state = 'confirmed'
        self.confirmation_date = fields.Datetime.now()
        
        # Log confirmation
        self.env['drkds.change.log'].log_change(
            action_type='update',
            object_model=self._name,
            object_id=self.id,
            object_name=self.name,
            description=f'Cost sheet "{self.name}" confirmed'
        )
    
    def action_reset_to_draft(self):
        """Reset to draft state"""
        self.ensure_one()
        self.state = 'draft'
        self.calculation_date = False
        self.confirmation_date = False
    
    def _calculate_all_formulas(self):
        """Main calculation engine"""
        # Build parameter context
        param_context = self._build_parameter_context()
        
        # Calculate each BOM line
        for line in self.bom_line_ids:
            if line.is_enabled:
                self._calculate_bom_line(line, param_context)
    
    def _build_parameter_context(self):
        """Build context dictionary for formula evaluation"""
        context = {
            'math': math,  # Allow math functions
        }
        
        # Add all parameters to context
        for param in self.parameter_line_ids:
            context[param.parameter_code] = param.get_numeric_value()
        
        # Add some common derived values
        context.update({
            'total_area': self.total_area,
            # Add more computed context as needed
        })
        
        return context
    
    def _calculate_bom_line(self, line, context):
        """Calculate individual BOM line"""
        template_comp = line.template_component_id
        
        # Calculate quantity
        if template_comp.quantity_formula:
            try:
                quantity = self._safe_eval(template_comp.quantity_formula, context)
                line.quantity = float(quantity) if quantity else 0.0
            except:
                line.quantity = 0.0
        
        # Calculate length
        if template_comp.length_formula:
            try:
                length = self._safe_eval(template_comp.length_formula, context)
                line.length_meter = float(length) if length else 0.0
            except:
                line.length_meter = 0.0
        
        # Calculate rate
        if template_comp.rate_formula:
            try:
                rate = self._safe_eval(template_comp.rate_formula, context)
                line.rate = float(rate) if rate else line.component_id.current_rate
            except:
                line.rate = line.component_id.current_rate
        else:
            line.rate = line.component_id.current_rate
    
    def _safe_eval(self, expression, context):
        """Safe evaluation of mathematical expressions"""
        if not expression:
            return 0
        
        # Define allowed names for security
        allowed_names = {
            "__builtins__": {"abs": abs, "min": min, "max": max, "round": round},
            "math": math,
        }
        allowed_names.update(context)
        
        try:
            # Parse and evaluate the expression safely
            node = ast.parse(expression, mode='eval')
            return eval(compile(node, '<string>', 'eval'), allowed_names)
        except Exception as e:
            raise UserError(_('Formula Error in "%s": %s') % (expression, str(e)))
    
    def action_duplicate(self):
        """Duplicate cost sheet"""
        new_sheet = self.copy({
            'name': f"{self.name} (Copy)",
            'state': 'draft',
            'calculation_date': False,
            'confirmation_date': False,
        })
        
        return {
            'name': _('Cost Sheet Copy'),
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': new_sheet.id,
            'type': 'ir.actions.act_window',
        }