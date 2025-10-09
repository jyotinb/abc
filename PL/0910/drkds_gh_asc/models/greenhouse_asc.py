from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class GreenhouseProject(models.Model):
    _inherit = 'greenhouse.project'
    
    total_asc_cost = fields.Float('Total ASC Cost', compute='_compute_asc_cost', store=True)
    
    @api.depends('component_line_ids.total_cost', 'component_line_ids.section')
    def _compute_asc_cost(self):
        for rec in self:
            asc_components = rec.component_line_ids.filtered(lambda c: c.section == 'asc')
            rec.total_asc_cost = sum(asc_components.mapped('total_cost'))
    
    def _calculate_all_components(self):
        """Add ASC calculations"""
        super()._calculate_all_components()
        if self.is_side_coridoors:
            self._calculate_asc_components()
        return True
    
    def _calculate_asc_components(self):
        """Calculate ASC components"""
        if not self.is_side_coridoors:
            return
        
        component_vals = []
        
        # ASC Pipe Support
        asc_support_count = (self.no_of_spans + 1) * 2 * 2
        component_vals.append({
            'project_id': self.id,
            'section': 'asc',
            'name': 'ASC Pipe Support',
            'nos': asc_support_count,
            'length': 2.5,
            'is_calculated': True,
        })
        
        # Front Span ASC Pipes
        front_span_count = 2 * 3
        component_vals.append({
            'project_id': self.id,
            'section': 'asc',
            'name': 'Front Span ASC Pipes',
            'nos': front_span_count,
            'length': self.span_length + 2.5,
            'is_calculated': True,
        })
        
        # Back Span ASC Pipes
        back_span_count = 2 * 3
        component_vals.append({
            'project_id': self.id,
            'section': 'asc',
            'name': 'Back Span ASC Pipes',
            'nos': back_span_count,
            'length': self.span_length + 2.5,
            'is_calculated': True,
        })
        
        # Front Bay ASC Pipes
        front_bay_count = (self.no_of_spans + 1) * 3
        component_vals.append({
            'project_id': self.id,
            'section': 'asc',
            'name': 'Front Bay ASC Pipes',
            'nos': front_bay_count,
            'length': 2.5,
            'is_calculated': True,
        })
        
        # Back Bay ASC Pipes
        back_bay_count = (self.no_of_spans + 1) * 3
        component_vals.append({
            'project_id': self.id,
            'section': 'asc',
            'name': 'Back Bay ASC Pipes',
            'nos': back_bay_count,
            'length': 2.5,
            'is_calculated': True,
        })
        
        # Create all component records
        for val in component_vals:
            self.env['greenhouse.component.line'].create(val)
            _logger.info(f"Created ASC component: {val['name']} - Nos: {val['nos']}")
