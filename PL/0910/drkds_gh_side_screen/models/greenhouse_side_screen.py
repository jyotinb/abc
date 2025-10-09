from odoo import models, fields, api
import logging
import math

_logger = logging.getLogger(__name__)

class GreenhouseProject(models.Model):
    _inherit = 'greenhouse.project'
    
    total_side_screen_cost = fields.Float('Total Side Screen Cost', compute='_compute_side_screen_cost', store=True)
    
    @api.depends('component_line_ids.total_cost', 'component_line_ids.section')
    def _compute_side_screen_cost(self):
        for rec in self:
            ss_components = rec.component_line_ids.filtered(lambda c: c.section == 'side_screen')
            rec.total_side_screen_cost = sum(ss_components.mapped('total_cost'))
    
    def _calculate_all_components(self):
        """Add side screen calculations"""
        super()._calculate_all_components()
        self._calculate_side_screen_components()
        return True
    
    def _calculate_side_screen_components(self):
        """Calculate side screen components"""
        component_vals = []
        
        # Side Screen Roll Up Pipe
        rollup_pipe_count = math.ceil(self.bay_length / 60) * self.no_of_curtains * 2
        component_vals.append({
            'project_id': self.id,
            'section': 'side_screen',
            'name': 'Side Screen Roll Up Pipe',
            'nos': rollup_pipe_count,
            'length': self.bay_length,
            'is_calculated': True,
        })
        
        # Roll Up Pipe Joiner
        if rollup_pipe_count > 2:
            joiners = (rollup_pipe_count - 2) * 2
            component_vals.append({
                'project_id': self.id,
                'section': 'side_screen',
                'name': 'Side Screen Roll Up Pipe Joiner',
                'nos': joiners,
                'length': 0.3,
                'is_calculated': True,
            })
        
        # Side Screen Guard
        if self.side_screen_guard:
            guard_count = 2 * 2  # Both sides
            component_vals.append({
                'project_id': self.id,
                'section': 'side_screen',
                'name': 'Side Screen Guard',
                'nos': guard_count,
                'length': self.bay_length,
                'is_calculated': True,
            })
            
            # Guard Spacer
            spacer_count = math.ceil(self.bay_length / 2.5) * 2 * 2
            component_vals.append({
                'project_id': self.id,
                'section': 'side_screen',
                'name': 'Side Screen Guard Spacer',
                'nos': spacer_count,
                'length': 0.2,
                'is_calculated': True,
            })
        
        # Side Screen Guard Box
        if self.side_screen_guard_box:
            component_vals.extend([
                {
                    'project_id': self.id,
                    'section': 'side_screen',
                    'name': 'Side Screen Guard Box Pipe',
                    'nos': 4,
                    'length': self.bay_length,
                    'is_calculated': True,
                },
                {
                    'project_id': self.id,
                    'section': 'side_screen',
                    'name': 'Side Screen Guard Box H Pipe',
                    'nos': math.ceil(self.bay_length / 2) * 4,
                    'length': 1.2,
                    'is_calculated': True,
                },
            ])
        
        # Rollup Handles
        handle_count = self.no_of_curtains * 2
        component_vals.append({
            'project_id': self.id,
            'section': 'side_screen',
            'name': 'Side Screen Rollup Handles',
            'nos': handle_count,
            'length': 1.5,
            'is_calculated': True,
        })
        
        # Create all component records
        for val in component_vals:
            self.env['greenhouse.component.line'].create(val)
            _logger.info(f"Created side screen component: {val['name']} - Nos: {val['nos']}")
