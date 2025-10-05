# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class GreenMasterFoundation(models.Model):
    _inherit = 'green.master'
    
    # Foundation configuration fields
    enable_foundation_rods = fields.Boolean('Enable Foundation Rods', default=False, tracking=True)
    foundation_rods_per_foundation = fields.Integer('Rods per Foundation', default=2, tracking=True)
    foundation_rods_per_asc = fields.Integer('Rods per ASC Pipe', default=2, tracking=True)
    
    def _calculate_all_accessories(self):
        """Extend to add foundation calculations"""
        super()._calculate_all_accessories()
        self._calculate_foundation_components()
    
    def _calculate_foundation_components(self):
        """Calculate foundation components"""
        self._calculate_foundation_rods()
    
    def _calculate_foundation_rods(self):
        """Calculate foundation rod requirements"""
        if not self.enable_foundation_rods:
            return
        
        # Get foundation count
        foundations_count = self._get_foundations_count()
        
        # Get ASC pipes count
        asc_pipes_count = self._get_asc_pipes_count()
        
        # Calculate total rods needed
        total_rods = (
            (foundations_count * self.foundation_rods_per_foundation) + 
            (asc_pipes_count * self.foundation_rods_per_asc)
        )
        
        if total_rods > 0:
            self._create_accessory_component(
                'foundation',
                'Foundation Rods',
                total_rods,
                'Standard'
            )
            _logger.info(f"Created Foundation Rods: {total_rods} pieces")
            _logger.info(f"  - From {foundations_count} foundations: {foundations_count * self.foundation_rods_per_foundation}")
            _logger.info(f"  - From {asc_pipes_count} ASC pipes: {asc_pipes_count * self.foundation_rods_per_asc}")
    
    def _get_foundations_count(self):
        """Get total number of foundations from frame components"""
        total_foundations = 0
        
        # Look for foundation-related components in frame
        foundation_components = self.frame_component_ids.filtered(
            lambda c: 'Foundations' in c.name and 'Columns' in c.name
        )
        
        for component in foundation_components:
            total_foundations += component.nos
        
        # If no specific foundation components, estimate from columns
        if total_foundations == 0:
            # Count main columns
            main_columns = self.frame_component_ids.filtered(
                lambda c: 'Main Columns' in c.name
            )
            if main_columns:
                total_foundations = main_columns.nos
            
            # Add thick columns
            thick_columns = self.frame_component_ids.filtered(
                lambda c: 'Thick Columns' in c.name
            )
            if thick_columns:
                total_foundations += thick_columns.nos
            
            # Add middle columns
            middle_columns = self.frame_component_ids.filtered(
                lambda c: c.name in ['Middle Columns', 'Quadruple Columns']
            )
            if middle_columns:
                total_foundations += middle_columns[0].nos
        
        return total_foundations
    
    def _get_asc_pipes_count(self):
        """Get total number of ASC pipes from ASC components"""
        total_asc_pipes = 0
        
        # Count all ASC pipe components
        asc_components = self.asc_component_ids.filtered(
            lambda c: 'ASC Pipes' in c.name
        )
        
        for component in asc_components:
            total_asc_pipes += component.nos
        
        return total_asc_pipes
    
    @api.onchange('enable_foundation_rods')
    def _onchange_enable_foundation_rods(self):
        """Handle foundation rods enable/disable"""
        if not self.enable_foundation_rods:
            self.foundation_rods_per_foundation = 2
            self.foundation_rods_per_asc = 2
    
    def action_calculate_foundation(self):
        """Action to calculate only foundation components"""
        for record in self:
            try:
                # Clear existing foundation components
                record.foundation_component_ids.unlink()
                
                # Calculate foundation
                record._calculate_foundation_components()
                
                foundations_count = record._get_foundations_count()
                asc_pipes_count = record._get_asc_pipes_count()
                component_count = len(record.foundation_component_ids)
                total_cost = record.total_foundation_cost
                
                message = f"FOUNDATION CALCULATION COMPLETED:\n\n"
                message += f"Foundations Detected: {foundations_count}\n"
                message += f"ASC Pipes Detected: {asc_pipes_count}\n"
                message += f"Rods per Foundation: {record.foundation_rods_per_foundation}\n"
                message += f"Rods per ASC: {record.foundation_rods_per_asc}\n\n"
                message += f"Components generated: {component_count}\n"
                message += f"Total Foundation Cost: {total_cost:.2f}"
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Foundation Calculated Successfully',
                        'message': message,
                        'type': 'success',
                        'sticky': True,
                    }
                }
            except Exception as e:
                _logger.error(f"Error in foundation calculation: {e}")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Foundation Calculation Error',
                        'message': f'Error occurred: {str(e)}',
                        'type': 'danger',
                    }
                }
