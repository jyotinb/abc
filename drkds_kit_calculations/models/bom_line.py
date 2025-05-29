from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CostBOMLine(models.Model):
    _name = 'drkds.cost.bom.line'
    _description = 'Cost Sheet BOM Line'
    _order = 'cost_sheet_id, sequence, component_id'
    
    # Relations
    cost_sheet_id = fields.Many2one('drkds.cost.sheet', string='Cost Sheet',
                                  required=True, ondelete='cascade')
    component_id = fields.Many2one('drkds.kit.component', string='Component',
                                 required=True)
    template_component_id = fields.Many2one('drkds.template.component', 
                                          string='Template Component')
    
    # Configuration
    sequence = fields.Integer(string='Sequence', default=10)
    
    # Component Toggle (Level 1 User Feature)
    is_enabled = fields.Boolean(string='Enabled', default=True)
    is_mandatory = fields.Boolean(string='Mandatory', default=False,
                                help="Mandatory components cannot be disabled")
    
    # Calculations
    quantity = fields.Float(string='Quantity', digits=(12, 3), default=0.0)
    length_meter = fields.Float(string='Length (Meter)', digits=(12, 3), default=0.0)
    rate = fields.Float(string='Rate', digits=(12, 2), default=0.0)
    amount = fields.Float(string='Amount', compute='_compute_amount', store=True, digits=(12, 2))
    rate_with_multiplier = fields.Float(string='Rate 1.2', compute='_compute_rate_multiplier', digits=(12, 2))
    
    # Helper Fields (Related)
    component_name = fields.Char(related='component_id.name', string='Component', store=True)
    component_code = fields.Char(related='component_id.code', string='Code')
    uom_name = fields.Char(related='component_id.uom_id.name', string='UOM')
    component_category = fields.Char(related='component_id.category_id.name', string='Category')
    
    # Status indicators
    has_quantity = fields.Boolean(string='Has Quantity', compute='_compute_status')
    has_rate = fields.Boolean(string='Has Rate', compute='_compute_status')
    is_calculated = fields.Boolean(string='Calculated', compute='_compute_status')
    
    @api.depends('quantity', 'rate', 'is_enabled')
    def _compute_amount(self):
        """Calculate line amount"""
        for line in self:
            if line.is_enabled and line.quantity and line.rate:
                line.amount = line.quantity * line.rate
            else:
                line.amount = 0.0
    
    @api.depends('rate', 'component_id.rate_multiplier')
    def _compute_rate_multiplier(self):
        """Calculate rate with multiplier"""
        for line in self:
            multiplier = line.component_id.rate_multiplier if line.component_id else 1.2
            line.rate_with_multiplier = line.rate * multiplier
    
    @api.depends('quantity', 'rate')
    def _compute_status(self):
        """Compute status indicators"""
        for line in self:
            line.has_quantity = line.quantity > 0
            line.has_rate = line.rate > 0
            line.is_calculated = line.has_quantity and line.has_rate
    
    def toggle_component(self):
        """Toggle component on/off - Available to Level 1 users"""
        self.ensure_one()
        
        # Check if component is mandatory
        if self.is_mandatory and self.is_enabled:
            raise ValidationError(_("Cannot disable mandatory component: %s") % self.component_name)
        
        # Toggle the component
        old_state = self.is_enabled
        self.is_enabled = not self.is_enabled
        
        # Log the change
        action = "enabled" if self.is_enabled else "disabled"
        self.env['drkds.change.log'].log_change(
            action_type='toggle',
            object_model=self._name,
            object_id=self.id,
            object_name=f"{self.cost_sheet_id.name} - {self.component_name}",
            field_name='is_enabled',
            old_value=old_state,
            new_value=self.is_enabled,
            description=f'Component "{self.component_name}" {action} in cost sheet "{self.cost_sheet_id.name}"'
        )
        
        # Recalculate totals
        self.cost_sheet_id._compute_totals()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Component Updated'),
                'message': _('Component %s %s') % (self.component_name, action),
                'type': 'success',
            }
        }
    
    def action_recalculate_line(self):
        """Recalculate this specific line"""
        self.ensure_one()
        if self.cost_sheet_id.state in ['calculated', 'confirmed']:
            # Build parameter context
            param_context = self.cost_sheet_id._build_parameter_context()
            # Recalculate this line
            self.cost_sheet_id._calculate_bom_line(self, param_context)
    
    @api.onchange('is_enabled')
    def _onchange_is_enabled(self):
        """Handle component enable/disable"""
        if not self.is_enabled and self.is_mandatory:
            self.is_enabled = True
            return {
                'warning': {
                    'title': _('Warning'),
                    'message': _('Cannot disable mandatory component: %s') % (self.component_name or 'Unknown')
                }
            }
    
    @api.constrains('quantity', 'rate')
    def _check_positive_values(self):
        """Ensure positive values for enabled components"""
        for line in self:
            if line.is_enabled:
                if line.quantity < 0:
                    raise ValidationError(_("Quantity cannot be negative for component: %s") % line.component_name)
                if line.rate < 0:
                    raise ValidationError(_("Rate cannot be negative for component: %s") % line.component_name)
    
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = f"{record.component_name}"
            if record.quantity:
                name += f" (Qty: {record.quantity})"
            if not record.is_enabled:
                name += " [DISABLED]"
            result.append((record.id, name))
        return result
    
    def write(self, vals):
        """Override write to log important changes"""
        # Log rate changes (Level 2 users)
        if 'rate' in vals:
            for record in self:
                old_rate = record.rate
                if old_rate != vals['rate']:
                    self.env['drkds.change.log'].log_change(
                        action_type='update',
                        object_model=self._name,
                        object_id=record.id,
                        object_name=f"{record.cost_sheet_id.name} - {record.component_name}",
                        field_name='rate',
                        old_value=old_rate,
                        new_value=vals['rate'],
                        description=f'Rate updated for "{record.component_name}" from {old_rate} to {vals["rate"]}'
                    )
        
        # Log quantity changes (from formula calculations)
        if 'quantity' in vals:
            for record in self:
                old_qty = record.quantity
                if abs(old_qty - vals['quantity']) > 0.001:  # Avoid logging tiny differences
                    self.env['drkds.change.log'].log_change(
                        action_type='calculation',
                        object_model=self._name,
                        object_id=record.id,
                        object_name=f"{record.cost_sheet_id.name} - {record.component_name}",
                        field_name='quantity',
                        old_value=old_qty,
                        new_value=vals['quantity'],
                        description=f'Quantity calculated for "{record.component_name}": {vals["quantity"]}'
                    )
        
        return super().write(vals)