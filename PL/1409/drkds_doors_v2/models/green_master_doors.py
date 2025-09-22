# -*- coding: utf-8 -*-
from odoo import models, fields, api
from math import ceil
import logging

_logger = logging.getLogger(__name__)

class GreenMaster(models.Model):
    _inherit = 'green.master'
    
    # =============================================
    # DOOR CONFIGURATION FIELDS
    # =============================================
    has_doors = fields.Boolean('Include Doors', default=False, tracking=True,
                              help="Enable door and chamber calculations")
    
    standalone_doors_count = fields.Integer('Standalone Doors (X)', default=0, tracking=True,
                                          help="Number of simple door openings")
    
    entry_chambers_count = fields.Integer('Entry Chambers (Y)', default=0, tracking=True,
                                        help="Number of full entry chambers with columns and purlins")
    
    # Chamber Configuration
    chamber_depth = fields.Float('Chamber Depth (m)', default=2.0, tracking=True,
                                help="Depth of entry chambers for purlin calculations")
    
    chamber_column_length = fields.Many2one(
        'length.master', 
        string='Chamber Column Length',
        domain="[('available_for_fields.name', '=', 'length_chamber_column'), ('active', '=', True)]",
        tracking=True,
        help="Selectable length for front columns in chambers"
    )
    
    # Tractor Door Configuration  
    tractor_door_type = fields.Selection([
        ('none', 'None'),
        ('vertical', 'Vertical'),
        ('openable', 'Openable'),
    ], string='Tractor Door Type', default='none', tracking=True,
       help="Type of tractor door installation")
    
    tractor_door_height = fields.Float('Tractor Door Height (m)', default=3.0, tracking=True,
                                     help="Height for tractor door vertical pipes")
    
    nos_tractor_doors = fields.Integer('Number of Tractor Doors', default=0, tracking=True,
                                     help="Total number of tractor doors to install")
    
    # =============================================
    # LENGTH MASTER FIELDS FOR DOOR COMPONENTS
    # =============================================
    length_column_pipe = fields.Many2one(
        'length.master', 
        string='Length for Door Column Pipe',
        domain="[('available_for_fields.name', '=', 'length_column_pipe'), ('active', '=', True)]",
        tracking=True
    )
    
    length_purlin_pipe = fields.Many2one(
        'length.master', 
        string='Length for Door Purlin Pipe',
        domain="[('available_for_fields.name', '=', 'length_purlin_pipe'), ('active', '=', True)]",
        tracking=True
    )
    
    length_tractor_door_purlin = fields.Many2one(
        'length.master', 
        string='Length for Tractor Door Purlin',
        domain="[('available_for_fields.name', '=', 'length_tractor_door_purlin'), ('active', '=', True)]",
        tracking=True
    )
    
    length_tractor_door_h_pipes = fields.Many2one(
        'length.master', 
        string='Length for Tractor Door H Pipes',
        domain="[('available_for_fields.name', '=', 'length_tractor_door_h_pipes'), ('active', '=', True)]",
        tracking=True
    )
    
    length_tractor_door_big_h_pipes = fields.Many2one(
        'length.master', 
        string='Length for Tractor Door Big H Pipes',
        domain="[('available_for_fields.name', '=', 'length_tractor_door_big_h_pipes'), ('active', '=', True)]",
        tracking=True
    )
    
    length_tractor_door_v_pipes = fields.Many2one(
        'length.master', 
        string='Length for Tractor Door V Pipes',
        domain="[('available_for_fields.name', '=', 'length_tractor_door_v_pipes'), ('active', '=', True)]",
        tracking=True
    )
    
    # =============================================
    # DOOR COMPONENT LINES AND TOTALS
    # =============================================
    door_component_ids = fields.One2many('component.line', 'green_master_id', 
                                        domain=[('section', '=', 'doors')], 
                                        string='Door Components')
    
    # Computed Totals
    total_door_components = fields.Integer('Total Door Components (X + Y)', 
                                         compute='_compute_door_totals', store=True,
                                         help="Total doors and chambers combined")
    
    total_chamber_components = fields.Integer('Total Chamber Components (Y)', 
                                            compute='_compute_door_totals', store=True,
                                            help="Entry chambers only")
    
    total_door_cost = fields.Float('Total Door Cost', 
                                  compute='_compute_door_totals', store=True, tracking=True)

    # =============================================
    # COMPUTED METHODS
    # =============================================
    @api.depends('standalone_doors_count', 'entry_chambers_count', 'door_component_ids.total_cost')
    def _compute_door_totals(self):
        """Compute door totals using the formula: Door Components = X + Y, Chamber Components = Y"""
        for record in self:
            record.total_door_components = record.standalone_doors_count + record.entry_chambers_count
            record.total_chamber_components = record.entry_chambers_count
            record.total_door_cost = sum(record.door_component_ids.mapped('total_cost'))

    @api.depends('asc_component_ids.total_cost', 'frame_component_ids.total_cost', 
                 'truss_component_ids.total_cost', 'side_screen_component_ids.total_cost',
                 'lower_component_ids.total_cost', 'door_component_ids.total_cost')
    def _compute_section_totals(self):
        """Override Green2's section totals computation to include doors"""
        for record in self:
            # Compute existing Green2 totals
            record.total_asc_cost = sum(record.asc_component_ids.mapped('total_cost'))
            record.total_frame_cost = sum(record.frame_component_ids.mapped('total_cost'))
            record.total_truss_cost = sum(record.truss_component_ids.mapped('total_cost'))
            record.total_side_screen_cost = sum(record.side_screen_component_ids.mapped('total_cost'))
            record.total_lower_cost = sum(record.lower_component_ids.mapped('total_cost'))
            
            # Add door costs to grand total
            record.grand_total_cost = (record.total_asc_cost + record.total_frame_cost + 
                                     record.total_truss_cost + record.total_side_screen_cost + 
                                     record.total_lower_cost + record.total_door_cost)

    # =============================================
    # ONCHANGE METHODS
    # =============================================
    @api.onchange('has_doors')
    def _onchange_has_doors(self):
        """Reset door counts when doors disabled"""
        if not self.has_doors:
            self.standalone_doors_count = 0
            self.entry_chambers_count = 0
            self.tractor_door_type = 'none'
            self.nos_tractor_doors = 0

    @api.onchange('tractor_door_type')
    def _onchange_tractor_door_type(self):
        """Reset tractor door count when type is none"""
        if self.tractor_door_type == 'none':
            self.nos_tractor_doors = 0

    # =============================================
    # CORE CALCULATION METHODS
    # =============================================
    def _calculate_all_components(self):
        """EXTEND Green2's _calculate_all_components to include door calculations"""
        # Call Green2's original calculation method first
        super()._calculate_all_components()
        
        # Then calculate door components
        if self.has_doors:
            self._calculate_door_components()

    def _calculate_door_components(self):
        """Calculate door components based on configuration"""
        if not self.has_doors:
            return
            
        component_vals = []
        
        # =============================================
        # STANDALONE DOORS (X) CALCULATIONS
        # =============================================
        if self.standalone_doors_count > 0:
            # Door Column Pipe: 1 piece × 3.5 MTR length (or selected length)
            column_pipe_length = self._get_door_length_master_value(self.length_column_pipe, 3.5)
            component_vals.append(self._create_door_component_val(
                'Door Column Pipe', 
                self.standalone_doors_count, 
                column_pipe_length, 
                self.length_column_pipe
            ))
            
            # Door Purlin Pipe: 1 piece × Bay Width length (or selected length)
            purlin_pipe_length = self._get_door_length_master_value(self.length_purlin_pipe, self.bay_width)
            component_vals.append(self._create_door_component_val(
                'Door Purlin Pipe', 
                self.standalone_doors_count, 
                purlin_pipe_length, 
                self.length_purlin_pipe
            ))
        
        # =============================================
        # ENTRY CHAMBERS (Y) CALCULATIONS
        # =============================================
        if self.entry_chambers_count > 0:
            # Get selected column length from user or default to 3.0m
            selected_column_length = self.chamber_column_length.length_value if self.chamber_column_length else 3.0
            
            # Door Front Column: 3 pieces × Selected Length per chamber
            component_vals.append(self._create_door_component_val(
                'Door Front Column', 
                self.entry_chambers_count * 3,  # 3 pieces per chamber
                selected_column_length, 
                self.chamber_column_length
            ))
            
            # Door Front Purlin: 1 piece × Bay Width per chamber
            component_vals.append(self._create_door_component_val(
                'Door Front Purlin', 
                self.entry_chambers_count, 
                self.bay_width
            ))
            
            # Door Side Purlin: 2 pieces × Chamber Depth per chamber
            component_vals.append(self._create_door_component_val(
                'Door Side Purlin', 
                self.entry_chambers_count * 2,  # 2 pieces per chamber
                self.chamber_depth
            ))
            
            # Door Bottom Purlin: 2 pieces × (Chamber Depth + 0.25) per chamber
            component_vals.append(self._create_door_component_val(
                'Door Bottom Purlin', 
                self.entry_chambers_count * 2,  # 2 pieces per chamber
                self.chamber_depth + 0.25
            ))
        
        # =============================================
        # TRACTOR DOOR CALCULATIONS
        # =============================================
        if self.tractor_door_type != 'none' and self.nos_tractor_doors > 0:
            
            if self.tractor_door_type == 'vertical':
                # VERTICAL TRACTOR DOOR COMPONENTS
                
                # Tractor Door Purlin: Nos = Nos of Tractor Doors, Length = Bay Width
                tractor_purlin_length = self._get_door_length_master_value(
                    self.length_tractor_door_purlin, self.bay_width)
                component_vals.append(self._create_door_component_val(
                    'Tractor Door Purlin', 
                    self.nos_tractor_doors, 
                    tractor_purlin_length,
                    self.length_tractor_door_purlin
                ))
                
                # Tractor Door H Pipes: Nos = 2 * Nos of Tractor Doors, Length = Bay Width / 2
                tractor_h_pipes_length = self._get_door_length_master_value(
                    self.length_tractor_door_h_pipes, self.bay_width / 2)
                component_vals.append(self._create_door_component_val(
                    'Tractor Door H Pipes', 
                    self.nos_tractor_doors * 2, 
                    tractor_h_pipes_length,
                    self.length_tractor_door_h_pipes
                ))
                
                # Tractor Door Big H Pipes: Nos = 2 * Nos of Tractor Doors, Length = Bay Width
                tractor_big_h_pipes_length = self._get_door_length_master_value(
                    self.length_tractor_door_big_h_pipes, self.bay_width)
                component_vals.append(self._create_door_component_val(
                    'Tractor Door Big H Pipes', 
                    self.nos_tractor_doors * 2, 
                    tractor_big_h_pipes_length,
                    self.length_tractor_door_big_h_pipes
                ))
                
                # Tractor Door V Pipes: Nos = 3 * Nos of Tractor Doors, Length = Tractor Door Height
                tractor_v_pipes_length = self._get_door_length_master_value(
                    self.length_tractor_door_v_pipes, self.tractor_door_height)
                component_vals.append(self._create_door_component_val(
                    'Tractor Door V Pipes', 
                    self.nos_tractor_doors * 3, 
                    tractor_v_pipes_length,
                    self.length_tractor_door_v_pipes
                ))
                
            elif self.tractor_door_type == 'openable':
                # OPENABLE TRACTOR DOOR COMPONENTS
                
                # Tractor Door Purlin: Nos = Nos of Tractor Doors, Length = Bay Width
                tractor_purlin_length = self._get_door_length_master_value(
                    self.length_tractor_door_purlin, self.bay_width)
                component_vals.append(self._create_door_component_val(
                    'Tractor Door Purlin', 
                    self.nos_tractor_doors, 
                    tractor_purlin_length,
                    self.length_tractor_door_purlin
                ))
                
                # Tractor Door H Pipes: Nos = 6 * Nos of Tractor Doors, Length = Bay Width / 2
                tractor_h_pipes_length = self._get_door_length_master_value(
                    self.length_tractor_door_h_pipes, self.bay_width / 2)
                component_vals.append(self._create_door_component_val(
                    'Tractor Door H Pipes', 
                    self.nos_tractor_doors * 6, 
                    tractor_h_pipes_length,
                    self.length_tractor_door_h_pipes
                ))
                
                # Tractor Door V Pipes: Nos = 4 * Nos of Tractor Doors, Length = Tractor Door Height
                tractor_v_pipes_length = self._get_door_length_master_value(
                    self.length_tractor_door_v_pipes, self.tractor_door_height)
                component_vals.append(self._create_door_component_val(
                    'Tractor Door V Pipes', 
                    self.nos_tractor_doors * 4, 
                    tractor_v_pipes_length,
                    self.length_tractor_door_v_pipes
                ))
        
        # Create all door component lines
        for val in component_vals:
            try:
                self.env['component.line'].create(val)
                _logger.info(f"Created door component: {val['name']} - Nos: {val['nos']} - Length: {val['length']}")
            except Exception as e:
                _logger.error(f"Error creating door component {val.get('name', 'Unknown')}: {e}")

    # =============================================
    # SELECTION PRESERVATION METHODS (EXTEND GREEN2'S PATTERN)
    # =============================================
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

    def _save_component_selections_improved(self):
        """EXTEND Green2's selection saving to include doors"""
        saved_selections = super()._save_component_selections_improved()
        
        # Add door components to saved selections
        door_components = self.door_component_ids or self.env['component.line']
        
        for component in door_components:
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
        
        return saved_selections

    def _restore_component_selections_improved(self, saved_selections):
        """EXTEND Green2's selection restoration to include doors"""
        restoration_result = super()._restore_component_selections_improved(saved_selections)
        
        # Restore door component selections
        door_components = self.door_component_ids or self.env['component.line']
        
        for component in door_components:
            component_key = self._generate_component_key(component.section, component.name)
            
            if component_key in saved_selections:
                selection_data = saved_selections[component_key]
                
                try:
                    update_vals = self._build_component_update_values(selection_data)
                    component.write(update_vals)
                    restoration_result['restored_count'] += 1
                    
                except Exception as e:
                    error_msg = f"Door Component: {component.name}, Error: {str(e)}"
                    restoration_result['failed_restorations'].append(error_msg)
        
        return restoration_result

    def _generate_recalculation_feedback(self, saved_selections, restoration_result, counts_before, counts_after):
        """EXTEND Green2's feedback generation to include doors"""
        total_before = sum(counts_before.values())
        total_after = sum(counts_after.values())
        
        message_parts = [
            f"RECALCULATION SUMMARY:",
            f"",
            f"Components Before: {total_before} | Components After: {total_after}",
            f"",
            f"SECTION BREAKDOWN:",
        ]
        
        # Include doors in section breakdown
        for section in ['asc', 'frame', 'truss', 'side_screen', 'lower', 'doors']:
            section_name = section.upper().replace('_', ' ')
            before_count = counts_before.get(section, 0)
            after_count = counts_after.get(section, 0)
            
            if before_count > 0 or after_count > 0:
                change_indicator = "↗" if after_count > before_count else "↘" if after_count < before_count else "→"
                message_parts.append(f"  {change_indicator} {section_name}: {before_count} → {after_count}")
        
        message_parts.extend([
            f"",
            f"PIPE SELECTIONS:",
            f"  • Saved: {len(saved_selections)} selections",
            f"  • Restored: {restoration_result['restored_count']} selections",
        ])
        
        if restoration_result.get('failed_restorations'):
            message_parts.extend([
                f"  ⚠ Failed to restore: {len(restoration_result['failed_restorations'])} selections",
                f"     (Check logs for details)"
            ])
        
        new_components = restoration_result.get('total_new_components', 0) - restoration_result.get('restored_count', 0)
        if new_components > 0:
            message_parts.append(f"  ✨ New components: {new_components} (need pipe selection)")
        
        message_parts.extend([
            f"",
            f"Door Configuration Summary:",
            f"  • Standalone Doors: {self.standalone_doors_count}",
            f"  • Entry Chambers: {self.entry_chambers_count}",
            f"  • Tractor Doors: {self.nos_tractor_doors} ({self.tractor_door_type})",
            f"",
            f"Current Total Cost: {self.grand_total_cost:,.2f}",
            f"",
            f"✅ Recalculation completed successfully!"
        ])
        
        return "\n".join(message_parts)

    # =============================================
    # HELPER METHODS
    # =============================================
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
            'description': f"Auto-calculated door/chamber component",
        }
        
        if length_master:
            val.update({
                'length_master_id': length_master.id,
                'use_length_master': True,
            })
        
        return val

    # =============================================
    # VALIDATION METHODS
    # =============================================
    @api.constrains('standalone_doors_count', 'entry_chambers_count', 'nos_tractor_doors')
    def _check_door_counts(self):
        """Validate door configuration"""
        for record in self:
            if record.has_doors:
                if record.standalone_doors_count < 0:
                    raise ValidationError("Standalone doors count cannot be negative")
                if record.entry_chambers_count < 0:
                    raise ValidationError("Entry chambers count cannot be negative")
                if record.nos_tractor_doors < 0:
                    raise ValidationError("Tractor doors count cannot be negative")
                
                # At least one type should be configured if doors are enabled
                total_doors = record.standalone_doors_count + record.entry_chambers_count + record.nos_tractor_doors
                if total_doors == 0:
                    raise ValidationError("At least one door type must be configured when doors are enabled")

    @api.constrains('chamber_depth', 'tractor_door_height')
    def _check_door_dimensions(self):
        """Validate door dimensions"""
        for record in self:
            if record.chamber_depth <= 0:
                raise ValidationError("Chamber depth must be greater than 0")
            if record.tractor_door_height <= 0:
                raise ValidationError("Tractor door height must be greater than 0")


# =============================================
# EXTEND COMPONENT LINE TO ADD DOORS SECTION
# =============================================
class ComponentLine(models.Model):
    _inherit = 'component.line'
    
    # Add 'doors' to Green2's existing section selection
    section = fields.Selection(
        selection_add=[('doors', 'Door Components')],
        ondelete={'doors': 'cascade'}
    )