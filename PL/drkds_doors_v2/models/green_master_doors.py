# -*- coding: utf-8 -*-
from odoo import models, fields, api
from math import ceil
import logging

_logger = logging.getLogger(__name__)

class GreenMaster(models.Model):
    _inherit = 'green.master'
    
    # Door Configuration Fields - Simplified
    has_doors = fields.Boolean('Include Doors', default=False, tracking=True)
    standalone_doors_count = fields.Integer('Standalone Doors (X)', default=0, tracking=True)
    entry_chambers_count = fields.Integer('Entry Chambers (Y)', default=0, tracking=True)
    
    # Essential Parameters Only
    chamber_depth = fields.Float('Chamber Depth (m)', default=2.0, 
                                help="Depth of entry chambers for purlin calculations")
    
    # Chamber Column Length Selection
    chamber_column_length = fields.Many2one(
        'length.master', 
        string='Chamber Column Length',
        domain="[('available_for_fields.name', '=', 'length_chamber_column'), ('active', '=', True)]",
        help="Selectable length for front columns in chambers"
    )
    
    # Tractor Door Configuration
    tractor_door_type = fields.Selection([
        ('none', 'None'),
        ('vertical', 'Vertical'),
        ('openable', 'Openable'),
    ], string='Tractor Door Type', default='none', tracking=True)
    
    tractor_door_height = fields.Float('Tractor Door Height (m)', default=3.0,
                                     help="Height for tractor door vertical and horizontal pipes")
    nos_tractor_doors = fields.Integer('Number of Tractor Doors', default=0,
                                     help="Total number of tractor doors")
    
    # Length Master Fields for New Components
    length_column_pipe = fields.Many2one(
        'length.master', 
        string='Length for Door Column Pipe',
        domain="[('available_for_fields.name', '=', 'length_column_pipe'), ('active', '=', True)]"
    )
    length_purlin_pipe = fields.Many2one(
        'length.master', 
        string='Length for Door Purlin Pipe',
        domain="[('available_for_fields.name', '=', 'length_purlin_pipe'), ('active', '=', True)]"
    )
    
    # Tractor Door Length Masters
    length_tractor_door_purlin = fields.Many2one(
        'length.master', 
        string='Length for Tractor Door Purlin',
        domain="[('available_for_fields.name', '=', 'length_tractor_door_purlin'), ('active', '=', True)]"
    )
    length_tractor_door_h_pipes = fields.Many2one(
        'length.master', 
        string='Length for Tractor Door H Pipes',
        domain="[('available_for_fields.name', '=', 'length_tractor_door_h_pipes'), ('active', '=', True)]"
    )
    length_tractor_door_big_h_pipes = fields.Many2one(
        'length.master', 
        string='Length for Tractor Door Big H Pipes',
        domain="[('available_for_fields.name', '=', 'length_tractor_door_big_h_pipes'), ('active', '=', True)]"
    )
    length_tractor_door_v_pipes = fields.Many2one(
        'length.master', 
        string='Length for Tractor Door V Pipes',
        domain="[('available_for_fields.name', '=', 'length_tractor_door_v_pipes'), ('active', '=', True)]"
    )
    
    # Door Component Lines - Using Green2's component.line exactly
    door_component_ids = fields.One2many('component.line', 'green_master_id', 
                                        domain=[('section', '=', 'doors')], 
                                        string='Door Components')
    
    # Door Totals - Your formula implementation
    total_door_components = fields.Integer('Total Door Components (X + Y)', 
                                         compute='_compute_door_totals', store=True)
    total_chamber_components = fields.Integer('Total Chamber Components (Y)', 
                                            compute='_compute_door_totals', store=True)
    total_door_cost = fields.Float('Total Door Cost', compute='_compute_door_totals', store=True)

    @api.depends('standalone_doors_count', 'entry_chambers_count', 'door_component_ids.total_cost')
    def _compute_door_totals(self):
        """Compute door totals using your exact formula"""
        for record in self:
            # Your Formula: Door Components = X + Y, Chamber Components = Y
            record.total_door_components = record.standalone_doors_count + record.entry_chambers_count
            record.total_chamber_components = record.entry_chambers_count
            record.total_door_cost = sum(record.door_component_ids.mapped('total_cost'))

    # PROPERLY OVERRIDE Green2's _compute_section_totals method
    @api.depends('asc_component_ids.total_cost', 'frame_component_ids.total_cost', 
                 'truss_component_ids.total_cost', 'lower_component_ids.total_cost', 'door_component_ids.total_cost')
    def _compute_section_totals(self):
        """Override Green2's section totals computation to include doors"""
        for record in self:
            # Compute existing Green2 totals
            record.total_asc_cost = sum(record.asc_component_ids.mapped('total_cost'))
            record.total_frame_cost = sum(record.frame_component_ids.mapped('total_cost'))
            record.total_truss_cost = sum(record.truss_component_ids.mapped('total_cost'))
            record.total_lower_cost = sum(record.lower_component_ids.mapped('total_cost'))
            
            # Add door costs to grand total
            record.grand_total_cost = (record.total_asc_cost + record.total_frame_cost + 
                                     record.total_truss_cost + record.total_lower_cost + record.total_door_cost)

    @api.onchange('has_doors')
    def _onchange_has_doors(self):
        """Reset door counts when doors disabled"""
        if not self.has_doors:
            self.standalone_doors_count = 0
            self.entry_chambers_count = 0

    # EXTEND Green2's action_calculate_process method - EXACT NAME FROM GREEN2
    def action_calculate_process(self):
        """
        EXTEND Green2's action_calculate_process to include door components
        This is Green2's main calculation method that we need to extend
        """
        for record in self:
            try:
                # Save all existing selections including doors (Green2 pattern)
                _logger.info(f"Starting component recalculation for {record.customer or 'Unnamed Project'}")
                saved_selections = record._save_component_selections_improved()
                
                # Clear all existing components including doors
                component_counts_before = {
                    'asc': len(record.asc_component_ids),
                    'frame': len(record.frame_component_ids),
                    'truss': len(record.truss_component_ids),
                    'lower': len(record.lower_component_ids),
                    'doors': len(record.door_component_ids),
                }
                
                record.asc_component_ids.unlink()
                record.frame_component_ids.unlink()
                record.truss_component_ids.unlink()
                record.lower_component_ids.unlink()
                record.door_component_ids.unlink()  # Clear door components too
                
                # Generate fresh components with new calculations (Green2 pattern)
                record._calculate_all_components()
                
                # Restore user selections (Green2 pattern)
                restoration_result = record._restore_component_selections_improved(saved_selections)
                
                # Count new components including doors
                component_counts_after = {
                    'asc': len(record.asc_component_ids),
                    'frame': len(record.frame_component_ids),
                    'truss': len(record.truss_component_ids),
                    'lower': len(record.lower_component_ids),
                    'doors': len(record.door_component_ids),
                }
                
                # Generate feedback message (Green2 pattern)
                feedback_message = record._generate_recalculation_feedback(
                    saved_selections, restoration_result, 
                    component_counts_before, component_counts_after
                )
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Components Recalculated Successfully',
                        'message': feedback_message,
                        'type': 'success',
                        'sticky': True,
                    }
                }
                
            except Exception as e:
                _logger.error(f"Error during component recalculation: {e}")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Recalculation Error',
                        'message': f'An error occurred during recalculation: {str(e)}',
                        'type': 'danger',
                    }
                }

    # EXTEND Green2's _calculate_all_components method - EXACT NAME FROM GREEN2
    def _calculate_all_components(self):
        """EXTEND Green2's _calculate_all_components to include door calculations"""
        # Call Green2's original calculation method first
        super()._calculate_all_components()
        
        # Then calculate door components
        self._calculate_door_components()

    def _calculate_door_components(self):
        """Calculate door components with NEW specifications and UPDATED names"""
        if not self.has_doors:
            return
            
        component_vals = []
        
        # =============================================
        # STANDALONE DOORS (X) - UPDATED NAMES
        # =============================================
        if self.standalone_doors_count > 0:
            # Door Column Pipe: 1 piece × 3.5 MTR length
            column_pipe_length = self._get_door_length_master_value(self.length_column_pipe, 3.5)
            component_vals.append(self._create_door_component_val(
                'Door Column Pipe', 
                self.standalone_doors_count, 
                column_pipe_length, 
                self.length_column_pipe
            ))
            
            # Door Purlin Pipe: 1 piece × Bay Width is length
            purlin_pipe_length = self._get_door_length_master_value(self.length_purlin_pipe, self.bay_width)
            component_vals.append(self._create_door_component_val(
                'Door Purlin Pipe', 
                self.standalone_doors_count, 
                purlin_pipe_length, 
                self.length_purlin_pipe
            ))
        
        # =============================================
        # ENTRY CHAMBERS (Y) - UPDATED NAMES  
        # =============================================
        if self.entry_chambers_count > 0:
            # Get selected column length from user or default
            selected_column_length = self.chamber_column_length.length_value if self.chamber_column_length else 3.0
            
            # Door Front Column: 3 pieces × Selected Length
            component_vals.append(self._create_door_component_val(
                'Door Front Column', 
                self.entry_chambers_count * 3,  # 3 pieces per chamber
                selected_column_length, 
                self.chamber_column_length
            ))
            
            # Door Front Purlin: 1 piece × Bay Width
            component_vals.append(self._create_door_component_val(
                'Door Front Purlin', 
                self.entry_chambers_count, 
                self.bay_width
            ))
            
            # Door Side Purlin: 2 pieces × Chamber Depth
            component_vals.append(self._create_door_component_val(
                'Door Side Purlin', 
                self.entry_chambers_count * 2,  # 2 pieces per chamber
                self.chamber_depth
            ))
            
            # Door Bottom Purlin: 2 pieces × (Chamber Depth + 0.25)
            component_vals.append(self._create_door_component_val(
                'Door Bottom Purlin', 
                self.entry_chambers_count * 2,  # 2 pieces per chamber
                self.chamber_depth + 0.25
            ))
        
        # =============================================
        # TRACTOR DOORS - NEW FUNCTIONALITY
        # =============================================
        if self.tractor_door_type != 'none' and self.nos_tractor_doors > 0:
            
            if self.tractor_door_type == 'vertical':
                # Vertical Tractor Door Components
                
                # Tractor Door Purlin: Nos = Nos of Tractor Doors, Length = Bay Width
                tractor_purlin_length = self._get_door_length_master_value(self.length_tractor_door_purlin, self.bay_width)
                component_vals.append(self._create_door_component_val(
                    'Tractor Door Purlin', 
                    self.nos_tractor_doors, 
                    tractor_purlin_length,
                    self.length_tractor_door_purlin
                ))
                
                # Tractor Door H Pipes: Nos = 2 * Nos of Tractor Doors, Length = Bay Width / 2
                tractor_h_pipes_length = self._get_door_length_master_value(self.length_tractor_door_h_pipes, self.bay_width / 2)
                component_vals.append(self._create_door_component_val(
                    'Tractor Door H Pipes', 
                    self.nos_tractor_doors * 2, 
                    tractor_h_pipes_length,
                    self.length_tractor_door_h_pipes
                ))
                
                # Tractor Door Big H Pipes: Nos = 2 * Nos of Tractor Doors, Length = Bay Width
                tractor_big_h_pipes_length = self._get_door_length_master_value(self.length_tractor_door_big_h_pipes, self.bay_width)
                component_vals.append(self._create_door_component_val(
                    'Tractor Door Big H Pipes', 
                    self.nos_tractor_doors * 2, 
                    tractor_big_h_pipes_length,
                    self.length_tractor_door_big_h_pipes
                ))
                
                # Tractor Door V Pipes: Nos = 3 * Nos of Tractor Doors, Length = Tractor Door Height
                tractor_v_pipes_length = self._get_door_length_master_value(self.length_tractor_door_v_pipes, self.tractor_door_height)
                component_vals.append(self._create_door_component_val(
                    'Tractor Door V Pipes', 
                    self.nos_tractor_doors * 3, 
                    tractor_v_pipes_length,
                    self.length_tractor_door_v_pipes
                ))
                
            elif self.tractor_door_type == 'openable':
                # Openable Tractor Door Components
                
                # Tractor Door Purlin: Nos = Nos of Tractor Doors, Length = Bay Width
                tractor_purlin_length = self._get_door_length_master_value(self.length_tractor_door_purlin, self.bay_width)
                component_vals.append(self._create_door_component_val(
                    'Tractor Door Purlin', 
                    self.nos_tractor_doors, 
                    tractor_purlin_length,
                    self.length_tractor_door_purlin
                ))
                
                # Tractor Door H Pipes: Nos = 6 * Nos of Tractor Doors, Length = Bay Width / 2
                tractor_h_pipes_length = self._get_door_length_master_value(self.length_tractor_door_h_pipes, self.bay_width / 2)
                component_vals.append(self._create_door_component_val(
                    'Tractor Door H Pipes', 
                    self.nos_tractor_doors * 6, 
                    tractor_h_pipes_length,
                    self.length_tractor_door_h_pipes
                ))
                
                # Tractor Door V Pipes: Nos = 4 * Nos of Tractor Doors, Length = Tractor Door Height
                tractor_v_pipes_length = self._get_door_length_master_value(self.length_tractor_door_v_pipes, self.tractor_door_height)
                component_vals.append(self._create_door_component_val(
                    'Tractor Door V Pipes', 
                    self.nos_tractor_doors * 4, 
                    tractor_v_pipes_length,
                    self.length_tractor_door_v_pipes
                ))
        
        # Create all door component lines using Green2's pattern
        for val in component_vals:
            try:
                self.env['component.line'].create(val)
            except Exception as e:
                _logger.error(f"Error creating door component {val.get('name', 'Unknown')}: {e}")

    # EXTEND Green2's _generate_component_key method - EXACT NAME FROM GREEN2
    def _generate_component_key(self, section, name):
        """EXTEND Green2's component key generation to handle doors"""
        if section == 'doors':
            # Door-specific key generation following Green2's pattern
            clean_name = name.strip().lower()
            name_mappings = {
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
            normalized_name = name_mappings.get(clean_name, clean_name.replace(' ', '_'))
            return f"{section}|{normalized_name}"
        else:
            # Call Green2's original method for other sections
            return super()._generate_component_key(section, name)

    def _get_door_length_master_value(self, length_master_field, default_value):
        """Get length from master field - Following Green2's helper pattern"""
        if length_master_field:
            try:
                return length_master_field.length_value
            except Exception:
                pass
        return default_value

    def _create_door_component_val(self, name, nos, length, length_master=None):
        """Create door component val - Following Green2's _create_component_val pattern"""
        val = {
            'green_master_id': self.id,
            'section': 'doors',
            'name': name,
            'required': True,
            'nos': int(nos),
            'length': length,
            'is_calculated': True,
            'description': f"Auto-calculated structural component for doors/chambers",
        }
        
        if length_master:
            val.update({
                'length_master_id': length_master.id,
                'use_length_master': True,
            })
        
        return val

# EXTEND Green2's ComponentLine to add doors section
class ComponentLine(models.Model):
    _inherit = 'component.line'
    
    # Add 'doors' to Green2's existing section selection
    section = fields.Selection(
        selection_add=[('doors', 'Door Components')],
        ondelete={'doors': 'cascade'}
    )