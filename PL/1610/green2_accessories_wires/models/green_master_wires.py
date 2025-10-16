# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class GreenMasterWires(models.Model):
    _inherit = 'green.master'
    
    # Wire configuration fields
    enable_zigzag_wire = fields.Boolean('Enable Zigzag Wire', default=False, tracking=True)
    zigzag_wire_size = fields.Selection([
        ('1.4', '1.4'),
        ('1.5', '1.5'),
        ('1.6', '1.6')
    ], string='Zigzag Wire Size', default='1.4', tracking=True)
    
    enable_rollup_connectors = fields.Boolean('Enable Roll Up Connectors', default=False, tracking=True)
    
    def _calculate_all_accessories(self):
        """Extend to add wire calculations"""
        super()._calculate_all_accessories()
        self._calculate_wire_components()
    
    def _calculate_wire_components(self):
        """Calculate wire and connector components"""
        self._calculate_zigzag_wire()
        self._calculate_rollup_connectors()
    
    def _calculate_zigzag_wire(self):
        """Calculate zigzag wire requirements"""
        if not self.enable_zigzag_wire:
            return
            
        # Get total profile length (if profiles module is installed)
        total_profile = 0
        if hasattr(self, 'total_profile'):
            total_profile = self.total_profile
        else:
            # Fallback calculation
            total_profile = self._estimate_total_profile()
        
        if total_profile > 0:
            self._create_accessory_component(
                'wires_connectors',
                f'Zigzag Wire {self.zigzag_wire_size}',
                int(total_profile),
                self.zigzag_wire_size
            )
            _logger.info(f"Created Zigzag Wire: {total_profile}m of {self.zigzag_wire_size}")
    
    def _calculate_rollup_connectors(self):
        """Calculate roll up connector requirements"""
        # Only calculate if both rollup connectors are enabled AND there are curtains
        if not self.enable_rollup_connectors or self.no_of_curtains <= 0:
            return
            
        # Roll Up Connector Smooth
        self._create_accessory_component(
            'wires_connectors',
            'Roll Up Connector Smooth',
            self.no_of_curtains,
            'Standard'
        )
        
        # Roll Up Connector Handle
        self._create_accessory_component(
            'wires_connectors',
            'Roll Up Connector Handle',
            self.no_of_curtains,
            'Standard'
        )
        
        _logger.info(f"Created Roll Up Connectors: {self.no_of_curtains} Smooth, {self.no_of_curtains} Handle")
        
    # ADD THIS NEW METHOD
    @api.onchange('no_of_curtains')
    def _onchange_no_of_curtains(self):
        """Disable roll up connectors when no curtains"""
        if self.no_of_curtains <= 0:
            self.enable_rollup_connectors = False
    
    def _estimate_total_profile(self):
        """Estimate total profile if profiles module not installed"""
        # Basic estimation based on structure dimensions
        estimated = 0
        
        # Arch profiles
        if hasattr(self, 'small_arch_length') and hasattr(self, 'big_arch_length'):
            arch_length = self.small_arch_length + self.big_arch_length
            if hasattr(self, 'no_of_spans'):
                estimated += arch_length * self.no_of_spans * 2
        
        # Purlin profiles
        if hasattr(self, 'span_length') and hasattr(self, 'no_of_bays'):
            estimated += self.span_length * (self.no_of_bays + 1) * 4
        
        return estimated
    
    @api.onchange('enable_zigzag_wire')
    def _onchange_enable_zigzag_wire(self):
        """Handle zigzag wire enable/disable"""
        if not self.enable_zigzag_wire:
            self.zigzag_wire_size = '1.4'
    
    @api.onchange('enable_rollup_connectors')
    def _onchange_enable_rollup_connectors(self):
        """Handle roll up connectors enable/disable"""
        if self.enable_rollup_connectors and self.no_of_curtains <= 0:
            # Show warning or set default
            pass
    
    def action_calculate_wires(self):
        """Action to calculate only wire components"""
        for record in self:
            try:
                # Clear existing wire components
                record.wires_connectors_component_ids.unlink()
                
                # Calculate wires
                record._calculate_wire_components()
                
                component_count = len(record.wires_connectors_component_ids)
                total_cost = record.total_wires_connectors_cost
                
                message = f"WIRES CALCULATION COMPLETED:\n\n"
                message += f"Components generated: {component_count}\n"
                message += f"Total Wires & Connectors Cost: {total_cost:.2f}"
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Wires Calculated Successfully',
                        'message': message,
                        'type': 'success',
                        'sticky': True,
                    }
                }
            except Exception as e:
                _logger.error(f"Error in wires calculation: {e}")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Wires Calculation Error',
                        'message': f'Error occurred: {str(e)}',
                        'type': 'danger',
                    }
                }
