from odoo import models, fields, api
from math import ceil
import logging

_logger = logging.getLogger(__name__)

class GreenMasterSideScreen(models.Model):
    _inherit = 'green.master'
    
    # Side Screen Configuration
    no_of_curtains = fields.Integer('No of Curtains', default=0, 
                                   help="Number of curtains for Side Screen Rollup Handles", 
                                   tracking=True)
    
    length_side_screen_rollup_handles = fields.Float('Length for Side Screen Rollup Handles', 
                                                    default=0.0, 
                                                    help="Manual entry for length of Side Screen Rollup Handles", 
                                                    tracking=True)
    
    side_screen_guard = fields.Boolean('Side Screen Guard', default=False, tracking=True)
    side_screen_guard_box = fields.Boolean('Side Screen Guard Box', default=False, tracking=True)
    no_side_screen_guard_box = fields.Integer('Number of Side Screen Guard Box', default=0, tracking=True)
    
    # Length Master Fields for Side Screen
    length_side_screen_roll_up_pipe_joiner = fields.Many2one(
        'length.master', 
        string='Length for Side Screen Roll Up Pipe Joiner',
        domain="[('available_for_fields.name', '=', 'length_side_screen_roll_up_pipe_joiner'), ('active', '=', True)]",
        tracking=True
    )
    
    length_side_screen_guard = fields.Many2one(
        'length.master', 
        string='Length for Side Screen Guard',
        domain="[('available_for_fields.name', '=', 'length_side_screen_guard'), ('active', '=', True)]",
        tracking=True
    )
    
    length_side_screen_guard_spacer = fields.Many2one(
        'length.master', 
        string='Length for Side Screen Guard Spacer',
        domain="[('available_for_fields.name', '=', 'length_side_screen_guard_spacer'), ('active', '=', True)]",
        tracking=True
    )
    
    length_side_screen_guard_box_h_pipe = fields.Many2one(
        'length.master', 
        string='Length for Side Screen Guard Box H Pipe',
        domain="[('available_for_fields.name', '=', 'length_side_screen_guard_box_h_pipe'), ('active', '=', True)]",
        tracking=True
    )
    
    @api.onchange('no_of_curtains')
    def _onchange_no_of_curtains(self):
        """Reset side screen settings when no_of_curtains is set to 0"""
        if self.no_of_curtains == 0:
            self.length_side_screen_rollup_handles = 0.0
            self.side_screen_guard = False
            self.side_screen_guard_box = False
            self.no_side_screen_guard_box = 0
    
    @api.onchange('side_screen_guard')
    def _onchange_side_screen_guard(self):
        """Reset guard-related settings when side_screen_guard is disabled"""
        if not self.side_screen_guard:
            self.side_screen_guard_box = False
            self.no_side_screen_guard_box = 0
    
    @api.onchange('side_screen_guard_box')
    def _onchange_side_screen_guard_box(self):
        if not self.side_screen_guard_box:
            self.no_side_screen_guard_box = 0
    
    def _calculate_all_components(self):
        """Extend calculation to add side screen components"""
        super()._calculate_all_components()
        self._calculate_side_screen_components()
    
    def _calculate_side_screen_components(self):
        """Calculate side screen-specific components"""
        component_vals = []
        
        # Calculate roll up pipe
        side_screen_roll_up_pipe = 0
        side_screen_roll_up_pipe_joiner = 0
        
        if self.no_of_curtains > 0 or self.side_screen_guard or self.side_screen_guard_box:
            side_screen_roll_up_pipe = ceil((self.bay_length / 5.95) * 2) + ceil((self.span_length / 5.95) * 2)
            side_screen_roll_up_pipe_joiner = int(side_screen_roll_up_pipe) - 4
        
        # Calculate guard components
        no_side_screen_guard = 0
        if self.side_screen_guard and self.no_of_curtains > 0:
            # Check if ASC is enabled
            no_total_hockeys = self._calculate_total_hockeys()
            no_side_screen_guard = no_total_hockeys if no_total_hockeys > 0 else ((self.no_of_spans + 1) * (self.no_of_bays + 1))
        
        # Rollup handles
        no_side_screen_rollup_handles = self.no_of_curtains if self.no_of_curtains > 0 else 0
        
        # Guard box components
        no_side_screen_guard_box_pipe = 0
        no_side_screen_guard_box_h_pipe = 0
        if self.no_side_screen_guard_box > 0 and self.no_of_curtains > 0:
            no_side_screen_guard_box_pipe = self.no_side_screen_guard_box * 2
            no_side_screen_guard_box_h_pipe = self.no_side_screen_guard_box * 2
        
        # Guard spacer
        side_screen_guard_spacer = 0
        if self.no_of_curtains > 0:
            side_screen_guard_spacer = (no_side_screen_guard * 2) + (self.no_side_screen_guard_box * 4)
        
        # Create components
        if side_screen_roll_up_pipe > 0:
            component_vals.append(self._create_component_val(
                'side_screen', 'Side Screen Roll Up Pipe', 
                side_screen_roll_up_pipe, 
                6.0
            ))
        
        if side_screen_roll_up_pipe_joiner > 0:
            joiner_length = self._get_length_master_value(self.length_side_screen_roll_up_pipe_joiner, 0.5)
            component_vals.append(self._create_component_val(
                'side_screen', 'Side Screen Roll Up Pipe Joiner', 
                side_screen_roll_up_pipe_joiner, 
                joiner_length,
                self.length_side_screen_roll_up_pipe_joiner
            ))
        
        if no_side_screen_rollup_handles > 0 and self.length_side_screen_rollup_handles > 0:
            component_vals.append(self._create_component_val(
                'side_screen', 'Side Screen Rollup Handles', 
                no_side_screen_rollup_handles, 
                self.length_side_screen_rollup_handles
            ))
        
        if no_side_screen_guard > 0:
            guard_length = self._get_length_master_value(self.length_side_screen_guard, 1.0)
            component_vals.append(self._create_component_val(
                'side_screen', 'Side Screen Guard', 
                no_side_screen_guard, 
                guard_length,
                self.length_side_screen_guard
            ))
        
        if no_side_screen_guard_box_pipe > 0:
            no_total_hockeys = self._calculate_total_hockeys()
            box_pipe_length = self.column_height
            if no_total_hockeys > 0:
                box_pipe_length = self.column_height + 1.5
            component_vals.append(self._create_component_val(
                'side_screen', 'Side Screen Guard Box Pipe', 
                no_side_screen_guard_box_pipe, 
                box_pipe_length
            ))
        
        if no_side_screen_guard_box_h_pipe > 0:
            box_h_pipe_length = self._get_length_master_value(self.length_side_screen_guard_box_h_pipe, 1.0)
            component_vals.append(self._create_component_val(
                'side_screen', 'Side Screen Guard Box H Pipe', 
                no_side_screen_guard_box_h_pipe, 
                box_h_pipe_length,
                self.length_side_screen_guard_box_h_pipe
            ))
        
        if side_screen_guard_spacer > 0:
            spacer_length = self._get_length_master_value(self.length_side_screen_guard_spacer, 0.3)
            component_vals.append(self._create_component_val(
                'side_screen', 'Side Screen Guard Spacer', 
                side_screen_guard_spacer, 
                spacer_length,
                self.length_side_screen_guard_spacer
            ))
        
        # Create all side screen component lines
        for val in component_vals:
            try:
                self.env['component.line'].create(val)
                _logger.info(f"Created side screen component: {val['name']} - Nos: {val['nos']} - Length: {val['length']}")
            except Exception as e:
                _logger.error(f"Error creating side screen component {val.get('name', 'Unknown')}: {e}")
    
    def _calculate_total_hockeys(self):
        """Calculate total hockeys if ASC is enabled - needed for side screen"""
        # This will be properly calculated when ASC module is installed
        # For now, return 0 (will be overridden by ASC module)
        return 0