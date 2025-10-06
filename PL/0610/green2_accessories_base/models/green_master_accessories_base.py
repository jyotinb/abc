# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class GreenMasterAccessoriesBase(models.Model):
    _inherit = 'green.master'
    
    # Base fields for all accessories
    accessories_component_ids = fields.One2many(
        'accessories.component.line',
        'green_master_id',
        string='Accessories Components'
    )
    
    # Section-specific component collections
    brackets_component_ids = fields.One2many(
        'accessories.component.line',
        'green_master_id',
        domain=[('section', '=', 'brackets')],
        string='Brackets Components'
    )
    
    wires_connectors_component_ids = fields.One2many(
        'accessories.component.line',
        'green_master_id',
        domain=[('section', '=', 'wires_connectors')],
        string='Wires & Connectors Components'
    )
    
    clamps_component_ids = fields.One2many(
        'accessories.component.line',
        'green_master_id',
        domain=[('section', '=', 'clamps')],
        string='Clamps Components'
    )
    
    profiles_component_ids = fields.One2many(
        'accessories.component.line',
        'green_master_id',
        domain=[('section', '=', 'profiles')],
        string='Profiles Components'
    )
    
    foundation_component_ids = fields.One2many(
        'accessories.component.line',
        'green_master_id',
        domain=[('section', '=', 'foundation')],
        string='Foundation Components'
    )
    
    # Cost fields
    total_profiles_cost = fields.Float(
        'Total Profiles Cost',
        compute='_compute_accessories_totals',
        store=True
    )
    
    total_brackets_cost = fields.Float(
        'Total Brackets Cost',
        compute='_compute_accessories_totals',
        store=True
    )
    
    total_wires_connectors_cost = fields.Float(
        'Total Wires & Connectors Cost',
        compute='_compute_accessories_totals',
        store=True
    )
    
    total_clamps_cost = fields.Float(
        'Total Clamps Cost',
        compute='_compute_accessories_totals',
        store=True
    )
    
    total_foundation_cost = fields.Float(
        'Total Foundation Cost',
        compute='_compute_accessories_totals',
        store=True
    )
    
    total_accessories_cost = fields.Float(
        'Total Accessories Cost',
        compute='_compute_accessories_totals',
        store=True
    )
    
    @api.depends('brackets_component_ids.total_cost', 
                 'wires_connectors_component_ids.total_cost',
                 'clamps_component_ids.total_cost', 
                 'foundation_component_ids.total_cost',
                 'profiles_component_ids.total_cost')
    def _compute_accessories_totals(self):
        """Compute total costs for each accessory section"""
        for record in self:
            record.total_brackets_cost = sum(record.brackets_component_ids.mapped('total_cost'))
            record.total_wires_connectors_cost = sum(record.wires_connectors_component_ids.mapped('total_cost'))
            record.total_clamps_cost = sum(record.clamps_component_ids.mapped('total_cost'))
            record.total_foundation_cost = sum(record.foundation_component_ids.mapped('total_cost'))
            record.total_profiles_cost = sum(record.profiles_component_ids.mapped('total_cost'))
            record.total_accessories_cost = (
                record.total_brackets_cost + 
                record.total_wires_connectors_cost + 
                record.total_clamps_cost + 
                record.total_foundation_cost + 
                record.total_profiles_cost
            )
    
    def _calculate_all_accessories(self):
        """Base method for accessories calculation - to be extended by specific modules"""
        saved_selections = self._save_accessories_selections()
        self._clear_accessories_components()
        # Each specific module will extend this method to add their calculations
        self._restore_accessories_selections(saved_selections)
    
    def _clear_accessories_components(self):
        """Clear all accessories component lines"""
        if self.accessories_component_ids:
            self.accessories_component_ids.unlink()
    
    def _create_accessory_component(self, section, name, nos, size_spec, custom_unit_price=None):
        """Reusable component creation method"""
        try:
            if nos <= 0:
                return None
                
            # Try to find matching master record
            master_record = None
            if custom_unit_price is None:
                master_record = self.env['accessories.master'].search([
                    ('name', '=', name),
                    ('category', '=', section),
                    ('active', '=', True)
                ], limit=1)
            
            unit_price = custom_unit_price if custom_unit_price is not None else (
                master_record.unit_price if master_record else 0.0
            )
            
            vals = {
                'green_master_id': self.id,
                'section': section,
                'name': name,
                'nos': int(nos),
                'size_specification': size_spec,
                'unit_price': unit_price,
                'is_calculated': True,
                'description': f"Auto-calculated accessory for {section} section",
            }
            
            if master_record:
                vals['accessories_master_id'] = master_record.id
            
            component = self.env['accessories.component.line'].create(vals)
            return component
            
        except Exception as e:
            _logger.error(f"Error creating accessory component {name}: {e}")
            return None
    
    def _save_accessories_selections(self):
        """Save current accessory selections before recalculation"""
        saved_selections = {}
        for component in self.accessories_component_ids:
            key = f"{component.section}_{component.name}"
            saved_selections[key] = {
                'unit_price': component.unit_price,
                'notes': component.notes or '',
                'accessories_master_id': component.accessories_master_id.id if component.accessories_master_id else False,
            }
        return saved_selections
    
    def _restore_accessories_selections(self, saved_selections):
        """Restore accessory selections after recalculation"""
        if not saved_selections:
            return
            
        for component in self.accessories_component_ids:
            key = f"{component.section}_{component.name}"
            if key in saved_selections:
                selection_data = saved_selections[key]
                try:
                    component.write({
                        'unit_price': selection_data['unit_price'],
                        'notes': selection_data['notes'],
                        'accessories_master_id': selection_data['accessories_master_id'],
                    })
                except Exception as e:
                    _logger.error(f"Failed to restore accessory selection for {component.name}: {e}")
    
    def action_calculate_accessories(self):
        """Action to calculate all accessories"""
        for record in self:
            try:
                record._calculate_all_accessories()
                component_count = len(record.accessories_component_ids)
                total_cost = record.total_accessories_cost
                message = f"ACCESSORIES CALCULATION COMPLETED:\n\nComponents generated: {component_count}\nTotal Accessories Cost: {total_cost:.2f}"
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Accessories Calculated Successfully',
                        'message': message,
                        'type': 'success',
                        'sticky': True,
                    }
                }
            except Exception as e:
                _logger.error(f"Error in accessories calculation: {e}")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Accessories Calculation Error',
                        'message': f'Error occurred: {str(e)}',
                        'type': 'danger',
                    }
                }
