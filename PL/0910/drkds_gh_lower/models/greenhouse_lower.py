from odoo import models, fields, api
import logging
import math

_logger = logging.getLogger(__name__)

class GreenhouseProject(models.Model):
    _inherit = 'greenhouse.project'
    
    total_lower_cost = fields.Float('Total Lower Cost', compute='_compute_lower_cost', store=True)
    
    @api.depends('component_line_ids.total_cost', 'component_line_ids.section')
    def _compute_lower_cost(self):
        for rec in self:
            lower_components = rec.component_line_ids.filtered(lambda c: c.section == 'lower')
            rec.total_lower_cost = sum(lower_components.mapped('total_cost'))
    
    def _calculate_all_components(self):
        """Add lower calculations"""
        super()._calculate_all_components()
        self._calculate_lower_components()
        return True
    
    def _calculate_lower_components(self):
        """Calculate lower section components"""
        component_vals = []
        
        # Cross Bracing calculations
        # Front & Back Column to Column Cross Bracing
        front_back_bracing = 2 * self.no_of_spans * 2
        component_vals.append({
            'project_id': self.id,
            'section': 'lower',
            'name': 'Front & Back Column to Column Cross Bracing X',
            'nos': front_back_bracing,
            'length': 2.0,
            'is_calculated': True,
        })
        
        # Internal CC Cross Bracing
        internal_bracing = (self.no_of_bays - 1) * (self.no_of_spans) * 2
        if internal_bracing > 0:
            component_vals.append({
                'project_id': self.id,
                'section': 'lower',
                'name': 'Internal CC Cross Bracing X',
                'nos': internal_bracing,
                'length': 2.0,
                'is_calculated': True,
            })
        
        # Cross Bracing Column to Arch
        if self.is_bottom_chord:
            cc_arch = 0  # No bracing when bottom chord exists
        else:
            cc_arch = self.no_of_spans * 2
        
        if cc_arch > 0:
            component_vals.append({
                'project_id': self.id,
                'section': 'lower',
                'name': 'Cross Bracing Column to Arch',
                'nos': cc_arch,
                'length': 2.0,
                'is_calculated': True,
            })
        
        # Cross Bracing Column to Bottom Chord
        if self.is_bottom_chord:
            cc_bottom = self.no_of_spans * 2
            component_vals.append({
                'project_id': self.id,
                'section': 'lower',
                'name': 'Cross Bracing Column to Bottom Chord',
                'nos': cc_bottom,
                'length': 2.0,
                'is_calculated': True,
            })
        
        # Arch Middle Purlins
        component_vals.extend([
            {
                'project_id': self.id,
                'section': 'lower',
                'name': 'Arch Middle Purlin Big Arch',
                'nos': (self.no_of_bays + 1) * 2,
                'length': self.span_length,
                'is_calculated': True,
            },
            {
                'project_id': self.id,
                'section': 'lower',
                'name': 'Arch Middle Purlin Small Arch',
                'nos': (self.no_of_bays + 1) * 2,
                'length': self.span_length,
                'is_calculated': True,
            },
        ])
        
        # Gutter System
        if self.gutter_type == 'ippf':
            # IPPF Gutter System
            gutter_full = self.no_of_bays * 2
            component_vals.append({
                'project_id': self.id,
                'section': 'lower',
                'name': 'Gutter IPPF Full',
                'nos': gutter_full,
                'length': self.gutter_length,
                'is_calculated': True,
            })
            
            # Calculate funnel and drainage
            funnel_count = math.ceil(self.gutter_length / 50) * self.no_of_bays * 2
            component_vals.extend([
                {
                    'project_id': self.id,
                    'section': 'lower',
                    'name': 'Gutter Funnel IPPF',
                    'nos': funnel_count,
                    'length': 0.3,
                    'is_calculated': True,
                },
                {
                    'project_id': self.id,
                    'section': 'lower',
                    'name': 'Gutter IPPF Drainage Extension',
                    'nos': self.no_of_bays * 4,
                    'length': 1.0,
                    'is_calculated': True,
                },
            ])
            
            # End Caps
            component_vals.append({
                'project_id': self.id,
                'section': 'lower',
                'name': 'Gutter End Cap',
                'nos': self.no_of_bays * 4,
                'length': 0.2,
                'is_calculated': True,
            })
        else:
            # Continuous Gutter
            component_vals.extend([
                {
                    'project_id': self.id,
                    'section': 'lower',
                    'name': 'Gutter Continuous',
                    'nos': self.no_of_bays * 2,
                    'length': self.gutter_length,
                    'is_calculated': True,
                },
                {
                    'project_id': self.id,
                    'section': 'lower',
                    'name': 'Gutter Purlin',
                    'nos': self.no_of_bays * 2 * 8,
                    'length': self.bay_width / 2,
                    'is_calculated': True,
                },
            ])
            
            if self.last_span_gutter and self.last_span_gutter_length > 0:
                component_vals.append({
                    'project_id': self.id,
                    'section': 'lower',
                    'name': 'Gutter Purlin for Extension',
                    'nos': self.no_of_bays * 2 * 4,
                    'length': self.last_span_gutter_length / 2,
                    'is_calculated': True,
                })
        
        # Create all component records
        for val in component_vals:
            self.env['greenhouse.component.line'].create(val)
            _logger.info(f"Created lower component: {val['name']} - Nos: {val['nos']}")
