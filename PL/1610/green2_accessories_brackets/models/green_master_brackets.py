# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class GreenMasterBrackets(models.Model):
    _inherit = 'green.master'
    
    # Bracket configuration fields
    gutter_bracket_type = fields.Selection([
        ('arch', 'Gutter Arch Bracket'),
        ('f_bracket', 'F Bracket'),
        ('none', 'None')
    ], string='Gutter Bracket Type', default='none', tracking=True)
    
    column_bracket_type = fields.Selection([
        ('l_bracket', 'L Bracket'),
        ('clamps', 'Clamps'),
        ('none', 'None')
    ], string='Column Bracket Type', default='none', tracking=True)
    
    # Computed field for F Bracket requirements
    f_bracket_big_count = fields.Integer(
        string='F Bracket Big Count',
        compute='_compute_f_bracket_counts',
        store=False
    )
    
    f_bracket_small_count = fields.Integer(
        string='F Bracket Small Count',
        compute='_compute_f_bracket_counts',
        store=False
    )
    
    
    def _get_big_arch_count(self):
        """Get count of big arch components"""
        if hasattr(self, 'truss_component_ids'):
            big_arch_component = self.truss_component_ids.filtered(
                lambda c: c.name == 'Big Arch'
            )
            return big_arch_component.nos if big_arch_component else 0
        return 0

    def _get_small_arch_count(self):
        """Get count of small arch components"""
        if hasattr(self, 'truss_component_ids'):
            small_arch_component = self.truss_component_ids.filtered(
                lambda c: c.name == 'Small Arch'
            )
            return small_arch_component.nos if small_arch_component else 0
        return 0

    def _get_middle_columns_count(self):
        """Get count of middle/quadruple columns"""
        if hasattr(self, 'frame_component_ids'):
            middle_columns = self.frame_component_ids.filtered(
                lambda c: c.name in ['Middle Columns', 'Quadruple Columns']
            )
            if middle_columns:
                return middle_columns[0].nos
        
        # Fallback calculation based on anchor frame configuration
        if hasattr(self, 'no_column_big_frame') and self.no_column_big_frame:
            if self.no_column_big_frame == '1':
                return self.no_anchor_frame_lines * self.no_of_spans
            elif self.no_column_big_frame in ['2', '3']:
                return self.no_anchor_frame_lines * self.no_of_spans * 2
        
        return 0
    
    @api.depends('gutter_bracket_type')
    def _compute_f_bracket_counts(self):
        """Compute F bracket requirements based on arch counts"""
        for record in self:
            if record.gutter_bracket_type == 'f_bracket':
                record.f_bracket_big_count = record._get_big_arch_count()
                record.f_bracket_small_count = record._get_small_arch_count()
            else:
                record.f_bracket_big_count = 0
                record.f_bracket_small_count = 0
    
    def _calculate_all_accessories(self):
        """Extend to add bracket calculations"""
        super()._calculate_all_accessories()
        self._calculate_bracket_components()
    
    def _calculate_bracket_components(self):
        """Calculate only bracket-related components"""
        self._calculate_gutter_brackets()
        self._calculate_column_brackets()
    
    def _calculate_gutter_brackets(self):
        """Calculate gutter bracket components based on type"""
        if self.gutter_bracket_type == 'arch':
            self._calculate_arch_brackets()
        elif self.gutter_bracket_type == 'f_bracket':
            self._calculate_f_brackets()
    
    def _calculate_arch_brackets(self):
        """Calculate Gutter Arch Bracket components"""
        if self.last_span_gutter:
            # All spans have gutters - full brackets everywhere
            qty = (self.no_of_spans + 1) * (self.no_of_bays + 1)
            self._create_accessory_component(
                'brackets', 
                'Gutter Arch Bracket HDGI 5.0 MM', 
                qty, 
                '5.0 MM'
            )
            _logger.info(f"Created {qty} Gutter Arch Brackets (last span gutter enabled)")
        else:
            # No gutter on last span - need half brackets for last span
            # Full brackets for middle spans
            qty_main = (self.no_of_spans - 1) * (self.no_of_bays + 1)
            if qty_main > 0:
                self._create_accessory_component(
                    'brackets', 
                    'Gutter Arch Bracket HDGI 5.0 MM', 
                    qty_main, 
                    '5.0 MM'
                )
                _logger.info(f"Created {qty_main} Gutter Arch Brackets (main)")
            
            # Half brackets for last span
            qty_half = self.no_of_bays + 1
            if qty_half > 0:
                self._create_accessory_component(
                    'brackets', 
                    'Gutter Arch Bracket HDGI Half Left', 
                    qty_half, 
                    'Half'
                )
                self._create_accessory_component(
                    'brackets', 
                    'Gutter Arch Bracket HDGI Half Right', 
                    qty_half, 
                    'Half'
                )
                _logger.info(f"Created {qty_half} Half Left and {qty_half} Half Right brackets")
    
    def _calculate_f_brackets(self):
        """Calculate F Bracket components"""
        # F Bracket Big - based on big arch count
        big_arch_count = self._get_big_arch_count()
        if big_arch_count > 0:
            self._create_accessory_component(
                'brackets', 
                'F Bracket Big', 
                big_arch_count, 
                'Big'
            )
            _logger.info(f"Created {big_arch_count} F Bracket Big")
        
        # F Bracket Small - based on small arch count
        small_arch_count = self._get_small_arch_count()
        if small_arch_count > 0:
            self._create_accessory_component(
                'brackets', 
                'F Bracket Small', 
                small_arch_count, 
                'Small'
            )
            _logger.info(f"Created {small_arch_count} F Bracket Small")
    
    def _calculate_column_brackets(self):
        """Calculate column bracket components"""
        middle_columns_count = self._get_middle_columns_count()
        
        if middle_columns_count <= 0:
            _logger.info("No middle columns found, skipping column brackets")
            return
        
        if self.column_bracket_type == 'l_bracket':
            # L Brackets - 2 per middle column
            qty = middle_columns_count * 2
            self._create_accessory_component(
                'brackets', 
                'L Bracket', 
                qty, 
                'Standard'
            )
            _logger.info(f"Created {qty} L Brackets for {middle_columns_count} middle columns")
            
        elif self.column_bracket_type == 'clamps':
            # Column Clamps - one per middle column
            # Note: Clamp size detection would be handled by the clamps module
            # Here we just note that clamps are needed
            pipe_size = self._get_middle_column_pipe_size()
            if pipe_size:
                # This would typically be handled by the clamps module
                # We're just logging here for clarity
                _logger.info(f"Column brackets set to clamps - {middle_columns_count} clamps needed (size: {pipe_size})")
    
    # Helper methods to get component counts
    def _get_big_arch_count(self):
        """Get count of big arch components"""
        big_arch_component = self.truss_component_ids.filtered(
            lambda c: c.name == 'Big Arch'
        )
        return big_arch_component.nos if big_arch_component else 0
    
    def _get_small_arch_count(self):
        """Get count of small arch components"""
        small_arch_component = self.truss_component_ids.filtered(
            lambda c: c.name == 'Small Arch'
        )
        return small_arch_component.nos if small_arch_component else 0
    
    def _get_middle_columns_count(self):
        """Get count of middle/quadruple columns"""
        middle_columns = self.frame_component_ids.filtered(
            lambda c: c.name in ['Middle Columns', 'Quadruple Columns']
        )
        if middle_columns:
            return middle_columns[0].nos
        
        # Fallback calculation based on anchor frame configuration
        if hasattr(self, 'no_column_big_frame') and self.no_column_big_frame:
            if self.no_column_big_frame == '1':
                return self.no_anchor_frame_lines * self.no_of_spans
            elif self.no_column_big_frame in ['2', '3']:
                return self.no_anchor_frame_lines * self.no_of_spans * 2
        
        return 0
    
    def _get_middle_column_pipe_size(self):
        """Get pipe size of middle columns for clamp sizing"""
        middle_columns = self.frame_component_ids.filtered(
            lambda c: c.name in ['Middle Columns', 'Quadruple Columns']
        )
        if middle_columns and middle_columns[0].pipe_id and middle_columns[0].pipe_id.pipe_size:
            return f"{middle_columns[0].pipe_id.pipe_size.size_in_mm:.0f}mm"
        return None
    
    @api.onchange('gutter_bracket_type')
    def _onchange_gutter_bracket_type(self):
        """Handle changes to gutter bracket type"""
        if self.gutter_bracket_type == 'none':
            # Clear any existing gutter bracket components when set to none
            pass
    
    @api.onchange('column_bracket_type')
    def _onchange_column_bracket_type(self):
        """Handle changes to column bracket type"""
        if self.column_bracket_type == 'none':
            # Clear any existing column bracket components when set to none
            pass
    
    def action_calculate_brackets(self):
        """Action to calculate only bracket components"""
        for record in self:
            try:
                # Clear existing bracket components
                record.brackets_component_ids.unlink()
                
                # Calculate brackets
                record._calculate_bracket_components()
                
                # Get selection labels
                gutter_type = dict(record._fields['gutter_bracket_type'].selection)[record.gutter_bracket_type]
                column_type = dict(record._fields['column_bracket_type'].selection)[record.column_bracket_type]
                component_count = len(record.brackets_component_ids)
                total_cost = record.total_brackets_cost
                
                message = f"BRACKETS CALCULATION COMPLETED:\n\n"
                message += f"Gutter Bracket Type: {gutter_type}\n"
                message += f"Column Bracket Type: {column_type}\n\n"
                message += f"Components generated: {component_count}\n"
                message += f"Total Brackets Cost: {total_cost:.2f}"
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Brackets Calculated Successfully',
                        'message': message,
                        'type': 'success',
                        'sticky': True,
                    }
                }
            except Exception as e:
                _logger.error(f"Error in brackets calculation: {e}")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Brackets Calculation Error',
                        'message': f'Error occurred: {str(e)}',
                        'type': 'danger',
                    }
                }
