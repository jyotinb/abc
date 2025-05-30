# File: drkds_kit_calculator/models/cost_sheet.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import ast
import operator
import math

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
            self.env['kit.cost.parameter'].create({
                'cost_sheet_id': self.id,
                'parameter_id': param.id,
                'value_float': float(param.default_value) if param.default_value and param.parameter_type == 'float' else 0.0,
                'value_integer': int(param.default_value) if param.default_value and param.parameter_type == 'integer' else 0,
                'value_char': param.default_value if param.parameter_type == 'char' else '',
                'value_boolean': param.default_value.lower() in ('true', '1') if param.parameter_type == 'boolean' else False,
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
                'rate': comp.component_id.current_rate,
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
        self.ensure_one()
        try:
            self._calculate_all_formulas()
            self.state = 'calculated'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Calculation completed successfully!'),
                    'type': 'success',
                }
            }
        except Exception as e:
            raise UserError(_('Calculation Error: %s') % str(e))
    
    def _calculate_all_formulas(self):
        # Build parameter context
        context = {'math': math}
        for param in self.parameter_ids:
            context[param.parameter_code] = param.get_numeric_value()
        
        # Calculate each component line
        for line in self.component_ids:
            if line.is_enabled and line.template_line_id:
                template_line = line.template_line_id
                
                # Calculate quantity
                if template_line.quantity_formula:
                    try:
                        quantity = self._safe_eval(template_line.quantity_formula, context)
                        line.quantity = float(quantity) if quantity else 0.0
                    except:
                        line.quantity = 0.0
                
                # Calculate rate
                if template_line.rate_formula:
                    try:
                        rate = self._safe_eval(template_line.rate_formula, context)
                        line.rate = float(rate) if rate else line.component_id.current_rate
                    except:
                        line.rate = line.component_id.current_rate
    
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
        
# File: Add this to the end of drkds_kit_calculator/models/cost_sheet.py

class KitCostParameter(models.Model):
    _name = 'kit.cost.parameter'
    _description = 'Kit Cost Parameter'
    
    cost_sheet_id = fields.Many2one('kit.cost.sheet', string='Cost Sheet', required=True, ondelete='cascade')
    parameter_id = fields.Many2one('kit.template.parameter', string='Parameter', required=True)
    
    # Parameter details
    parameter_name = fields.Char(related='parameter_id.name', store=True)
    parameter_code = fields.Char(related='parameter_id.code', store=True)
    parameter_type = fields.Selection(related='parameter_id.parameter_type')
    
    # Values
    value_float = fields.Float(string='Float Value', digits=(12, 3))
    value_integer = fields.Integer(string='Integer Value')
    value_char = fields.Char(string='Text Value')
    value_boolean = fields.Boolean(string='Boolean Value')
    
    def get_numeric_value(self):
        if self.parameter_type == 'float':
            return self.value_float
        elif self.parameter_type == 'integer':
            return float(self.value_integer)
        elif self.parameter_type == 'boolean':
            return 1.0 if self.value_boolean else 0.0
        else:
            try:
                return float(self.value_char or '0')
            except:
                return 0.0

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
    
    quantity = fields.Float(string='Quantity', digits=(12, 3), default=0.0)
    rate = fields.Float(string='Rate', digits=(12, 2), default=0.0)
    amount = fields.Float(string='Amount', compute='_compute_amount', store=True)
    
    # Related fields
    component_name = fields.Char(related='component_id.name', store=True)
    component_category = fields.Selection(related='component_id.category')
    uom = fields.Selection(related='component_id.uom')
    
    @api.depends('quantity', 'rate', 'is_enabled')
    def _compute_amount(self):
        for line in self:
            if line.is_enabled:
                line.amount = line.quantity * line.rate
            else:
                line.amount = 0.0
    
    def toggle_component(self):
        self.ensure_one()
        if self.is_mandatory and self.is_enabled:
            raise ValidationError(_("Cannot disable mandatory component."))
        self.is_enabled = not self.is_enabled