from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class GreenMasterFrame(models.Model):
    _inherit = 'green.master'
    
    # Frame Configuration Fields
    no_column_big_frame = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2'),('3', '3')
    ], string='No of Big Column per Anchor Frame', required=True, default='0', tracking=True)
    
    no_anchor_frame_lines = fields.Integer('Number of Anchor Frame Lines', default=0, tracking=True)
    
    thick_column = fields.Selection([
        ('0', '0'),
        ('1','4 Corners'),
        ('2','Both Bay Side'),
        ('3','Both Span Side'),
        ('4','All 4 Side')
    ], string='Thick Column Option', required=True, default='0', tracking=True)
    
    @api.onchange('no_column_big_frame')
    def _onchange_no_column_big_frame(self):
        if self.no_column_big_frame == '0':
            self.no_anchor_frame_lines = 0
    
    def _calculate_all_components(self):
        """Extend base calculation to add frame components"""
        super()._calculate_all_components()
        self._calculate_frame_components()
    
    def _calculate_frame_components(self):
        """Calculate frame-specific components"""
        component_vals = []
        
        # Calculate anchor frames
        total_anchor_frames = self.no_anchor_frame_lines * self.no_of_spans
        total_normal_frames = (self.no_of_spans * (self.no_of_bays + 1)) - total_anchor_frames
        
        # Calculate middle and quadruple columns
        no_middle_columns = 0
        no_quadraple_columns = 0
        if int(self.no_column_big_frame) == 1:
            no_middle_columns = total_anchor_frames
        elif int(self.no_column_big_frame) == 2:
            no_quadraple_columns = total_anchor_frames * 2
        elif int(self.no_column_big_frame) == 3:
            no_middle_columns = total_anchor_frames
            no_quadraple_columns = total_anchor_frames * 2
        
        # Calculate thick columns
        no_thick_columns = 0
        no_af_main_columns = 0
        no_main_columns = 0
        
        total_column_positions = (self.no_of_spans + 1) * (self.no_of_bays + 1)
        
        if self.thick_column == '0':  # No thick columns
            if self.no_anchor_frame_lines > 0:
                no_af_main_columns = self.no_anchor_frame_lines * (self.no_of_spans + 1)
            no_main_columns = total_column_positions - no_af_main_columns
        elif self.thick_column == '1':  # 4 Corners
            no_thick_columns = 4
            if self.no_anchor_frame_lines == 1:
                no_af_main_columns = (self.no_of_spans + 1) - 2
            elif self.no_anchor_frame_lines >= 2:
                no_af_main_columns = (2 * (self.no_of_spans + 1)) - 4
            else:
                no_af_main_columns = 0
            no_main_columns = total_column_positions - no_af_main_columns - no_thick_columns
        elif self.thick_column == '2':  # Both Bay Sides
            no_thick_columns = (self.no_of_bays + 1) * 2
            if self.no_anchor_frame_lines == 1:
                no_af_main_columns = (self.no_of_spans + 1) - 2
            elif self.no_anchor_frame_lines >= 2:
                no_af_main_columns = (self.no_anchor_frame_lines * (self.no_of_spans + 1)) - 4
            else:
                no_af_main_columns = 0
            no_main_columns = total_column_positions - no_af_main_columns - no_thick_columns
        elif self.thick_column == '3':  # Both Span Sides
            no_thick_columns = (self.no_of_spans + 1) * 2
            if self.no_anchor_frame_lines > 2:
                no_af_main_columns = (self.no_of_spans + 1) * (self.no_anchor_frame_lines - 2)
            else:
                no_af_main_columns = 0
            no_main_columns = total_column_positions - no_af_main_columns - no_thick_columns
        elif self.thick_column == '4':  # All 4 Sides
            no_thick_columns = ((self.no_of_spans + 1) * 2) + ((self.no_of_bays - 1) * 2)
            no_af_main_columns = 0
            no_main_columns = total_column_positions - no_thick_columns
        
        # Create column components
        if no_middle_columns > 0:
            component_vals.append(self._create_component_val(
                'frame', 'Middle Columns', 
                no_middle_columns, 
                self.top_ridge_height
            ))
        
        if no_quadraple_columns > 0:
            quadruple_column_length = self.column_height + ((self.top_ridge_height - self.column_height) * 0.6)
            component_vals.append(self._create_component_val(
                'frame', 'Quadruple Columns', 
                no_quadraple_columns, 
                quadruple_column_length
            ))
        
        if no_main_columns > 0:
            component_vals.append(self._create_component_val(
                'frame', 'Main Columns', 
                no_main_columns, 
                self.column_height
            ))
        
        if no_af_main_columns > 0:
            component_vals.append(self._create_component_val(
                'frame', 'AF Main Columns', 
                no_af_main_columns, 
                self.column_height
            ))
        
        if no_thick_columns > 0:
            component_vals.append(self._create_component_val(
                'frame', 'Thick Columns', 
                no_thick_columns, 
                self.column_height
            ))
        
        # Foundation components
        if self.foundation_length > 0:
            if no_main_columns > 0:
                component_vals.append(self._create_component_val(
                    'frame', 'Main Columns Foundations', 
                    no_main_columns, 
                    self.foundation_length
                ))
            
            if no_af_main_columns > 0:
                component_vals.append(self._create_component_val(
                    'frame', 'AF Main Columns Foundations', 
                    no_af_main_columns, 
                    self.foundation_length
                ))
            
            if no_middle_columns > 0:
                component_vals.append(self._create_component_val(
                    'frame', 'Middle Columns Foundations', 
                    no_middle_columns, 
                    self.foundation_length
                ))
            
            if no_quadraple_columns > 0:
                component_vals.append(self._create_component_val(
                    'frame', 'Quadruple Columns Foundations', 
                    no_quadraple_columns, 
                    self.foundation_length
                ))
            
            if no_thick_columns > 0:
                component_vals.append(self._create_component_val(
                    'frame', 'Thick Columns Foundations', 
                    no_thick_columns, 
                    self.foundation_length
                ))
        
        # Create all frame component lines
        for val in component_vals:
            try:
                self.env['component.line'].create(val)
                _logger.info(f"Created frame component: {val['name']} - Nos: {val['nos']} - Length: {val['length']}")
            except Exception as e:
                _logger.error(f"Error creating frame component {val.get('name', 'Unknown')}: {e}")