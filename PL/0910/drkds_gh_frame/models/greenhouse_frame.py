from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class GreenhouseProject(models.Model):
    _inherit = 'greenhouse.project'
    
    # Frame section costs
    total_frame_cost = fields.Float('Total Frame Cost', compute='_compute_frame_cost', store=True)
    
    @api.depends('component_line_ids.total_cost', 'component_line_ids.section')
    def _compute_frame_cost(self):
        for rec in self:
            frame_components = rec.component_line_ids.filtered(lambda c: c.section == 'frame')
            rec.total_frame_cost = sum(frame_components.mapped('total_cost'))
    
    def _calculate_all_components(self):
        """Add frame calculations"""
        super()._calculate_all_components()
        self._calculate_frame_components()
        return True
    
    def _calculate_frame_components(self):
        """Calculate frame-specific components"""
        component_vals = []
        
        # Calculate anchor frames
        total_anchor_frames = self.no_anchor_frame_lines * self.no_of_spans
        total_normal_frames = (self.no_of_spans * (self.no_of_bays + 1)) - total_anchor_frames
        
        # Calculate columns based on configuration
        no_middle_columns = 0
        no_quadruple_columns = 0
        
        if int(self.no_column_big_frame) == 1:
            no_middle_columns = total_anchor_frames
        elif int(self.no_column_big_frame) == 2:
            no_quadruple_columns = total_anchor_frames * 2
        elif int(self.no_column_big_frame) == 3:
            no_middle_columns = total_anchor_frames
            no_quadruple_columns = total_anchor_frames * 2
        
        # Calculate main columns
        total_column_positions = (self.no_of_spans + 1) * (self.no_of_bays + 1)
        no_thick_columns = 0
        no_af_main_columns = 0
        no_main_columns = 0
        
        if self.thick_column == '0':  # No thick columns
            if self.no_anchor_frame_lines > 0:
                no_af_main_columns = self.no_anchor_frame_lines * (self.no_of_spans + 1)
            no_main_columns = total_column_positions - no_af_main_columns
        elif self.thick_column == '1':  # 4 Corners
            no_thick_columns = 4
            if self.no_anchor_frame_lines > 0:
                no_af_main_columns = self.no_anchor_frame_lines * (self.no_of_spans + 1) - no_thick_columns
            no_main_columns = total_column_positions - no_af_main_columns - no_thick_columns
        elif self.thick_column == '2':  # Both Bay Side
            no_thick_columns = 2 * (self.no_of_bays + 1)
            remaining = total_column_positions - no_thick_columns
            if self.no_anchor_frame_lines > 0:
                no_af_main_columns = min(self.no_anchor_frame_lines * (self.no_of_spans + 1), remaining)
            no_main_columns = remaining - no_af_main_columns
        elif self.thick_column == '3':  # Both Span Side
            no_thick_columns = 2 * (self.no_of_spans + 1)
            remaining = total_column_positions - no_thick_columns
            if self.no_anchor_frame_lines > 0:
                no_af_main_columns = min(self.no_anchor_frame_lines * (self.no_of_spans + 1), remaining)
            no_main_columns = remaining - no_af_main_columns
        elif self.thick_column == '4':  # All 4 Side
            no_thick_columns = 2 * ((self.no_of_bays + 1) + (self.no_of_spans + 1)) - 4
            remaining = total_column_positions - no_thick_columns
            if self.no_anchor_frame_lines > 0:
                no_af_main_columns = min(self.no_anchor_frame_lines * (self.no_of_spans + 1), remaining)
            no_main_columns = remaining - no_af_main_columns
        
        # Create components
        if no_middle_columns > 0:
            component_vals.append({
                'project_id': self.id,
                'section': 'frame',
                'name': 'Middle Columns',
                'nos': no_middle_columns,
                'length': self.top_ridge_height,
                'is_calculated': True,
            })
        
        if no_quadruple_columns > 0:
            component_vals.append({
                'project_id': self.id,
                'section': 'frame',
                'name': 'Quadruple Columns',
                'nos': no_quadruple_columns,
                'length': self.column_height,
                'is_calculated': True,
            })
        
        if no_main_columns > 0:
            component_vals.append({
                'project_id': self.id,
                'section': 'frame',
                'name': 'Main Columns',
                'nos': no_main_columns,
                'length': self.column_height,
                'is_calculated': True,
            })
        
        if no_af_main_columns > 0:
            component_vals.append({
                'project_id': self.id,
                'section': 'frame',
                'name': 'AF Main Columns',
                'nos': no_af_main_columns,
                'length': self.column_height,
                'is_calculated': True,
            })
        
        if no_thick_columns > 0:
            component_vals.append({
                'project_id': self.id,
                'section': 'frame',
                'name': 'Thick Columns',
                'nos': no_thick_columns,
                'length': self.column_height,
                'is_calculated': True,
            })
        
        # Foundations
        if no_main_columns > 0:
            component_vals.append({
                'project_id': self.id,
                'section': 'frame',
                'name': 'Main Columns Foundations',
                'nos': no_main_columns,
                'length': self.foundation_length,
                'is_calculated': True,
            })
        
        if no_af_main_columns > 0:
            component_vals.append({
                'project_id': self.id,
                'section': 'frame',
                'name': 'AF Main Columns Foundations',
                'nos': no_af_main_columns,
                'length': self.foundation_length,
                'is_calculated': True,
            })
        
        if no_middle_columns > 0:
            component_vals.append({
                'project_id': self.id,
                'section': 'frame',
                'name': 'Middle Columns Foundations',
                'nos': no_middle_columns,
                'length': self.foundation_length,
                'is_calculated': True,
            })
        
        if no_quadruple_columns > 0:
            component_vals.append({
                'project_id': self.id,
                'section': 'frame',
                'name': 'Quadruple Columns Foundations',
                'nos': no_quadruple_columns,
                'length': self.foundation_length,
                'is_calculated': True,
            })
        
        if no_thick_columns > 0:
            component_vals.append({
                'project_id': self.id,
                'section': 'frame',
                'name': 'Thick Columns Foundations',
                'nos': no_thick_columns,
                'length': self.foundation_length,
                'is_calculated': True,
            })
        
        # Create all component records
        for val in component_vals:
            self.env['greenhouse.component.line'].create(val)
            _logger.info(f"Created frame component: {val['name']} - Nos: {val['nos']}")
    
    @api.onchange('no_column_big_frame')
    def _onchange_no_column_big_frame(self):
        """Reset anchor frames when changing column configuration"""
        if self.no_column_big_frame == '0':
            self.no_anchor_frame_lines = 0
