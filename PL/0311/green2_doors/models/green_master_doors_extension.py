# -*- coding: utf-8 -*-
from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class GreenMasterDoorsExtension(models.Model):
    """
    Extension to add doors support to base GreenMaster methods
    WITHOUT modifying the base module code
    """
    _inherit = 'green.master'
    
    # ═══════════════════════════════════════════════════════════════
    # EXTEND: Component Key Generation
    # ═══════════════════════════════════════════════════════════════
    def _generate_component_key(self, section, name):
        """Extend to handle door component keys"""
        # First call parent method
        key = super()._generate_component_key(section, name)
        
        # Add door-specific mappings if section is 'doors'
        if section == 'doors':
            clean_name = name.strip().lower()
            door_mappings = {
                'door column pipe': 'door_column_pipe',
                'door purlin pipe': 'door_purlin_pipe',
                'door front column': 'door_front_column',
                'door front purlin': 'door_front_purlin',
                'door side purlin': 'door_side_purlin',
                'door bottom purlin': 'door_bottom_purlin',
                'tractor door purlin': 'tractor_door_purlin',
                'tractor door h pipes': 'tractor_door_h_pipes',
                'tractor door big h pipes': 'tractor_door_big_h_pipes',
                'tractor door v pipes': 'tractor_door_v_pipes',
            }
            normalized_name = door_mappings.get(clean_name, clean_name.replace(' ', '_'))
            return f"{section}|{normalized_name}"
        
        return key
    
    # ═══════════════════════════════════════════════════════════════
    # EXTEND: Clear All Components
    # ═══════════════════════════════════════════════════════════════
    def _clear_all_components(self):
        """Override to also clear door components"""
        super()._clear_all_components()
        
        # Clear door components explicitly
        if hasattr(self, 'door_component_ids'):
            self.write({
                'door_component_ids': [(5, 0, 0)]
            })
            _logger.info("Cleared door components")
    
    # ═══════════════════════════════════════════════════════════════
    # EXTEND: Save Component Selections
    # ═══════════════════════════════════════════════════════════════
    def _save_component_selections_improved(self):
        """Override to include door components in save"""
        # Call parent to get base saved selections
        saved_selections = super()._save_component_selections_improved()
        
        # Add door components if they exist
        if hasattr(self, 'door_component_ids') and self.door_component_ids:
            for component in self.door_component_ids:
                component_key = self._generate_component_key(component.section, component.name)
                
                saved_selections[component_key] = {
                    'original_name': component.name,
                    'original_section': component.section,
                    'pipe_id': component.pipe_id.id if component.pipe_id else False,
                    'pipe_display_name': component.pipe_id.display_name if component.pipe_id else '',
                    'use_length_master': component.use_length_master,
                    'length_master_id': component.length_master_id.id if component.length_master_id else False,
                    'length_master_value': component.length_master_id.length_value if component.length_master_id else 0.0,
                    'custom_length': component.custom_length,
                    'required': component.required,
                    'notes': component.notes or '',
                    'description': component.description or '',
                    'section': component.section,
                }
            
            _logger.info(f"Saved {len(self.door_component_ids)} door component selections")
        
        return saved_selections
    
    # ═══════════════════════════════════════════════════════════════
    # EXTEND: Restore Component Selections
    # ═══════════════════════════════════════════════════════════════
    def _restore_component_selections_improved(self, saved_selections):
        """Override to include door components in restore"""
        # Call parent to restore base components
        restoration_result = super()._restore_component_selections_improved(saved_selections)
        
        # Restore door components
        if hasattr(self, 'door_component_ids') and self.door_component_ids:
            door_restored_count = 0
            
            for component in self.door_component_ids:
                component_key = self._generate_component_key(component.section, component.name)
                
                if component_key in saved_selections:
                    selection_data = saved_selections[component_key]
                    
                    try:
                        update_vals = self._build_component_update_values(selection_data)
                        component.write(update_vals)
                        door_restored_count += 1
                        
                    except Exception as e:
                        error_msg = f"Door Component: {component.name}, Error: {str(e)}"
                        restoration_result['failed_restorations'].append(error_msg)
            
            # Update restoration count
            restoration_result['restored_count'] += door_restored_count
            _logger.info(f"Restored {door_restored_count} door component selections")
        
        return restoration_result
    
    # ═══════════════════════════════════════════════════════════════
    # EXTEND: Clear Pipe Selections
    # ═══════════════════════════════════════════════════════════════
    def action_clear_pipe_selections(self):
        """Override to ensure door components are included"""
        # First clear door pipes
        if hasattr(self, 'door_component_ids'):
            for component in self.door_component_ids:
                if component.pipe_id:
                    component.pipe_id = False
            _logger.info("Cleared door pipe selections")
        
        # Then call parent to handle the rest and show notification
        return super().action_clear_pipe_selections()
    
    # ═══════════════════════════════════════════════════════════════
    # EXTEND: Component Count Methods (for statistics)
    # ═══════════════════════════════════════════════════════════════
    def _generate_recalculation_feedback(self, saved_selections, restoration_result, counts_before, counts_after):
        """Override to include door counts in feedback"""
        # Add door counts to the dictionaries
        if hasattr(self, 'door_component_ids'):
            if 'doors' not in counts_before:
                counts_before['doors'] = 0
            if 'doors' not in counts_after:
                counts_after['doors'] = 0
        
        # Call parent with updated counts
        return super()._generate_recalculation_feedback(
            saved_selections, restoration_result, counts_before, counts_after
        )
    
    # ═══════════════════════════════════════════════════════════════
    # EXTEND: Component Collection for Various Operations
    # ═══════════════════════════════════════════════════════════════
    def action_view_selection_summary(self):
        """Override to include doors in selection summary"""
        components_with_pipes = []
        components_without_pipes = []
        
        all_components = (self.frame_component_ids + self.truss_component_ids + 
                         self.side_screen_component_ids + self.lower_component_ids)
        
        if hasattr(self, 'asc_component_ids'):
            all_components = all_components + self.asc_component_ids
        
        # ADD DOOR COMPONENTS
        if hasattr(self, 'door_component_ids'):
            all_components = all_components + self.door_component_ids
        
        for component in all_components:
            if component.pipe_id:
                components_with_pipes.append(f"{component.section.upper()}: {component.name}")
            else:
                components_without_pipes.append(f"{component.section.upper()}: {component.name}")
        
        message = f"""PIPE SELECTION SUMMARY:

Components WITH pipe selections ({len(components_with_pipes)}):
{chr(10).join(components_with_pipes) if components_with_pipes else 'None'}

Components WITHOUT pipe selections ({len(components_without_pipes)}):
{chr(10).join(components_without_pipes) if components_without_pipes else 'None'}

Total Components: {len(all_components)}
Completion: {len(components_with_pipes)}/{len(all_components)} ({int(len(components_with_pipes)/len(all_components)*100) if all_components else 0}%)"""
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Pipe Selection Summary',
                'message': message,
                'type': 'info',
                'sticky': True,
            }
        }
    
    # ═══════════════════════════════════════════════════════════════
    # EXTEND: Duplication Support
    # ═══════════════════════════════════════════════════════════════
    def _save_all_components(self):
        """Override to include door components in duplication"""
        components_data = super()._save_all_components()
        
        # Add door components
        if hasattr(self, 'door_component_ids'):
            for component in self.door_component_ids:
                component_data = {
                    'section': component.section,
                    'sequence': component.sequence,
                    'name': component.name,
                    'description': component.description,
                    'required': component.required,
                    'notes': component.notes,
                    'nos': component.nos,
                    'length': component.length,
                    'use_length_master': component.use_length_master,
                    'length_master_id': component.length_master_id.id if component.length_master_id else False,
                    'custom_length': component.custom_length,
                    'pipe_id': component.pipe_id.id if component.pipe_id else False,
                    'is_calculated': component.is_calculated,
                }
                components_data.append(component_data)
        
        return components_data