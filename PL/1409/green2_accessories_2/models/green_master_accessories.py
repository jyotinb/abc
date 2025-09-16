# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from math import ceil
import logging

_logger = logging.getLogger(__name__)

class GreenMaster(models.Model):
    _inherit = 'green.master'
    
    # ==================== INPUT FIELDS ====================
    
    # Gutter Bracket Configuration
    gutter_bracket_type = fields.Selection([
        ('arch', 'Gutter Arch Bracket'),
        ('f_bracket', 'F Bracket'),
        ('none', 'None')
    ], string='Gutter Bracket Type', default='none', tracking=True)
    
    # Zigzag Wire Configuration
    enable_zigzag_wire = fields.Boolean('Enable Zigzag Wire', default=False, tracking=True)
    zigzag_wire_size = fields.Selection([
        ('1.4', '1.4'),
        ('1.5', '1.5'),
        ('1.6', '1.6')
    ], string='Zigzag Wire Size', default='1.4', tracking=True)
    
    # Column Bracket Configuration
    column_bracket_type = fields.Selection([
        ('l_bracket', 'L Bracket'),
        ('clamps', 'Clamps'),
        ('none', 'None')
    ], string='Column Bracket Type', default='none', tracking=True)
    
    # Roll Up Connectors Configuration
    enable_rollup_connectors = fields.Boolean('Enable Roll Up Connectors', default=False, tracking=True)
    
    # ==================== PROFILE FIELDS ====================
    
    profiles_for_arch = fields.Float('Profiles For Arch', compute='_compute_all_profiles', store=True)
    profile_for_purlin = fields.Float('Profile For Purlin', compute='_compute_all_profiles', store=True)
    profile_for_bottom = fields.Float('Profile for Bottom', compute='_compute_all_profiles', store=True)
    side_profile = fields.Float('Side Profile', compute='_compute_all_profiles', store=True)
    door_profile = fields.Float('Door Profile', compute='_compute_all_profiles', store=True)
    total_profile = fields.Float('Total Profile', compute='_compute_all_profiles', store=True)
    
    
    # Foundation Rods Configuration
    enable_foundation_rods = fields.Boolean('Enable Foundation Rods', default=False, tracking=True)
    foundation_rods_per_foundation = fields.Integer('Rods per Foundation', default=2, tracking=True)
    foundation_rods_per_asc = fields.Integer('Rods per ASC Pipe', default=2, tracking=True)
    
    # Advanced Clamp Configuration
    clamp_type = fields.Selection([
        ('w_type', 'W Type'),
        ('m_type', 'M Type'),
        ('none', 'None')
    ], string='Clamp Type', default='none', tracking=True)

    # W Type specific - Big Purlin
    big_purlin_clamp_type_first = fields.Selection([
        ('full_clamp', 'Full Clamp'),
        ('l_joint', 'L Joint'),
    ], string='Big Purlin First Type', tracking=True)

    big_purlin_clamp_type_second = fields.Selection([
        ('half_clamp', 'Half Clamp'),
        ('t_joint', 'T Joint'),
    ], string='Big Purlin Second Type', tracking=True)

    # W Type specific - Small Purlin
    small_purlin_clamp_type_first = fields.Selection([
        ('full_clamp', 'Full Clamp'),
        ('l_joint', 'L Joint'),
    ], string='Small Purlin First Type', tracking=True)

    small_purlin_clamp_type_second = fields.Selection([
        ('half_clamp', 'Half Clamp'),
        ('t_joint', 'T Joint'),
    ], string='Small Purlin Second Type', tracking=True)

    # M Type specific
    bottom_chord_clamp_type = fields.Selection([
        ('single', 'Single'),
        ('triple', 'Triple')
    ], string='Bottom Chord Clamp Type', default='single', tracking=True)
        
    
    # ==================== COMPONENT RELATIONSHIPS ====================
    
    # All accessories components
    accessories_component_ids = fields.One2many(
        'accessories.component.line', 
        'green_master_id', 
        string='Accessories Components'
    )
    
    # Section-wise components
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
    
    
    clamps_size_summary = fields.Text(
        string='Clamps Size Summary', 
        compute='_compute_clamps_size_summary',
        store=False
    )

    total_profiles_cost = fields.Float('Total Profiles Cost', 
                                      compute='_compute_accessories_totals', store=True, tracking=True)

    total_foundation_cost = fields.Float('Total Foundation Cost', 
                                      compute='_compute_accessories_totals', store=True, tracking=True)
    # ==================== COMPUTED TOTALS ====================
    
    total_brackets_cost = fields.Float('Total Brackets Cost', 
                                      compute='_compute_accessories_totals', store=True, tracking=True)
    total_wires_connectors_cost = fields.Float('Total Wires & Connectors Cost', 
                                              compute='_compute_accessories_totals', store=True, tracking=True)
    total_clamps_cost = fields.Float('Total Clamps Cost', 
                                    compute='_compute_accessories_totals', store=True, tracking=True)
    total_accessories_cost = fields.Float('Total Accessories Cost', 
                                         compute='_compute_accessories_totals', store=True, tracking=True)
    
    @api.depends('brackets_component_ids.total_cost', 'wires_connectors_component_ids.total_cost', 
                 'clamps_component_ids.total_cost', 'foundation_component_ids.total_cost')
    def _compute_accessories_totals(self):
        for record in self:
            record.total_brackets_cost = sum(record.brackets_component_ids.mapped('total_cost'))
            record.total_wires_connectors_cost = sum(record.wires_connectors_component_ids.mapped('total_cost'))
            record.total_clamps_cost = sum(record.clamps_component_ids.mapped('total_cost'))
            record.total_foundation_cost = sum(record.foundation_component_ids.mapped('total_cost'))
            record.total_accessories_cost = (record.total_brackets_cost + 
                                           record.total_wires_connectors_cost + 
                                           record.total_clamps_cost +
                                           record.total_foundation_cost +
                                           record.total_profiles_cost) 
    
    # ==================== PROFILE CALCULATIONS ====================
    
    @api.depends(
        'no_of_spans', 'span_length', 'small_arch_length', 'big_arch_length',
        'length_vent_big_arch_support', 'length_vent_small_arch_support',
        'truss_component_ids.total_length', 'lower_component_ids.total_length',
        'asc_component_ids.total_length', 'gutter_type', 'column_height', 
        'is_side_coridoors', 'bay_width', 'bay_length'
    )
    def _compute_all_profiles(self):
        """Compute all profile calculations"""
        for record in self:
            try:
                record.profiles_for_arch = record._calculate_profiles_for_arch()
                record.profile_for_purlin = record._calculate_profile_for_purlin()
                record.profile_for_bottom = record._calculate_profile_for_bottom()
                record.side_profile = record._calculate_side_profile()
                record.door_profile = record._calculate_door_profile()
                record.total_profile = record._calculate_total_profile()
                
            except Exception as e:
                _logger.error(f"Error computing profiles: {e}")
                record.profiles_for_arch = 0
                record.profile_for_purlin = 0
                record.profile_for_bottom = 0
                record.side_profile = 0
                record.door_profile = 0
                record.total_profile = 0
    
    def _calculate_profiles_for_arch(self):
        """Calculate Profiles For Arch"""
        try:
            if self.span_length <= 0 or self.no_of_spans <= 0:
                return 0
            # Get vent support lengths from length master or default values
            vent_big_length = 0
            vent_small_length = 0
            
            # Get vent support lengths from main structure fields
            if hasattr(self, 'length_vent_big_arch_support') and self.length_vent_big_arch_support:
                vent_big_length = self.length_vent_big_arch_support.length_value
            
            if hasattr(self, 'length_vent_small_arch_support') and self.length_vent_small_arch_support:
                vent_small_length = self.length_vent_small_arch_support.length_value
            
            # Formula: No of Spans * (Roundup((Span Length / 20)+1) * (Small Arch Length + Big Arch Length + Vent Support Length)
            roundup_factor = ceil((self.span_length / 20) + 1)
            arch_total_length = self.small_arch_length + self.big_arch_length + vent_big_length + vent_small_length
            profiles_for_arch = self.no_of_spans * roundup_factor * arch_total_length
            
            return profiles_for_arch
            
        except Exception as e:
            _logger.error(f"Error calculating profiles for arch: {e}")
            return 0

    def _calculate_profile_for_purlin(self):
        """Calculate Profile For Purlin"""
        try:
            total_purlin_profile = 0
            
            # (No of Big Arch Purlin * Length) + (No of Small Arch Purlin * Length)
            big_arch_purlin_component = self.truss_component_ids.filtered(lambda c: c.name == 'Big Arch Purlin')
            if big_arch_purlin_component:
                total_purlin_profile += big_arch_purlin_component.total_length
            
            small_arch_purlin_component = self.truss_component_ids.filtered(lambda c: c.name == 'Small Arch Purlin')
            if small_arch_purlin_component:
                total_purlin_profile += small_arch_purlin_component.total_length
            
            # Gutter calculations
            if self.gutter_type == 'continuous':
                # if continuous Gutter then (No of Gutter Purlin * Length)
                gutter_purlin_component = self.lower_component_ids.filtered(lambda c: c.name == 'Gutter Purlin')
                if gutter_purlin_component:
                    total_purlin_profile += gutter_purlin_component.total_length
                    
            elif self.gutter_type == 'ippf':
                # if IPPF Gutter then (Gutter Total Length *2)
                gutter_ippf_component = self.lower_component_ids.filtered(lambda c: c.name == 'Gutter IPPF Full')
                if gutter_ippf_component:
                    total_purlin_profile += gutter_ippf_component.total_length * 2
            
            # + (Gable Purlin Total Length)
            gable_purlin_component = self.truss_component_ids.filtered(lambda c: c.name == 'Gable Purlin')
            if gable_purlin_component:
                total_purlin_profile += gable_purlin_component.total_length
            
            return total_purlin_profile
            
        except Exception as e:
            _logger.error(f"Error calculating profile for purlin: {e}")
            return 0

    def _calculate_profile_for_bottom(self):
        """Calculate Profile for Bottom"""
        try:
            # Formula: Span Length * 2
            profile_for_bottom = self.span_length * 2
            return profile_for_bottom
            
        except Exception as e:
            _logger.error(f"Error calculating profile for bottom: {e}")
            return 0

    def _calculate_side_profile(self):
        """Calculate Side Profile"""
        try:
            side_profile = 0
            
            # Bay Side Border Purlin Total Length
            bay_border_component = self.truss_component_ids.filtered(lambda c: c.name == 'Bay Side Border Purlin')
            if bay_border_component:
                side_profile += bay_border_component.total_length
            
            # + Span Side Border Purlin Total Length
            span_border_component = self.truss_component_ids.filtered(lambda c: c.name == 'Span Side Border Purlin')
            if span_border_component:
                side_profile += span_border_component.total_length
            
            # + 8 * (if ASC then max ASC length else Main Column Length)
            multiplier_length = 0
            
            if self.is_side_coridoors:
                # Get all ASC component lengths and find maximum
                asc_lengths = []
                
                # Check all possible ASC component names
                asc_component_names = [
                    'Front Span ASC Pipes', 'Back Span ASC Pipes',
                    'Front Bay ASC Pipes', 'Back Bay ASC Pipes'
                ]
                
                for asc_name in asc_component_names:
                    asc_component = self.asc_component_ids.filtered(lambda c: asc_name in c.name)
                    if asc_component:
                        asc_lengths.append(asc_component.length)
                
                # Use maximum ASC length if available, otherwise use column height
                multiplier_length = max(asc_lengths) if asc_lengths else self.column_height
            else:
                # Use Main Column Length (column height)
                multiplier_length = self.column_height
            
            side_profile += 8 * multiplier_length
            
            return side_profile
            
        except Exception as e:
            _logger.error(f"Error calculating side profile: {e}")
            return 0

    def _calculate_door_profile(self):
        """Calculate Door Profile"""
        try:
            door_profile = 0
            
            # All door pipe Total Length
            if hasattr(self, 'door_component_ids') and self.door_component_ids:
                door_profile += sum(self.door_component_ids.mapped('total_length'))
            
            # All Tractor Door pipe Total Length (if exists)
            if hasattr(self, 'tractor_door_component_ids') and self.tractor_door_component_ids:
                door_profile += sum(self.tractor_door_component_ids.mapped('total_length'))
            
            return door_profile
            
        except Exception as e:
            _logger.error(f"Error calculating door profile: {e}")
            return 0

    def _calculate_total_profile(self):
        """Calculate Total Profile - Sum of all profiles"""
        try:
            profiles_for_arch = self._calculate_profiles_for_arch()
            profile_for_purlin = self._calculate_profile_for_purlin()
            profile_for_bottom = self._calculate_profile_for_bottom()
            side_profile = self._calculate_side_profile()
            door_profile = self._calculate_door_profile()
            
            total_profile = (profiles_for_arch + profile_for_purlin + 
                            profile_for_bottom + side_profile + door_profile)
            
            return total_profile
            
        except Exception as e:
            _logger.error(f"Error calculating total profile: {e}")
            return 0
            
            
    def _create_total_profile_component(self):
        """Create Total Profile as a component line for cost calculations"""
        if self.total_profile > 0:
            # Get default pricing from master data
            master_record = self.env['accessories.master'].search([
                ('name', '=', 'Total Profile'),
                ('category', '=', 'profiles'),
                ('active', '=', True)
            ], limit=1)
            
            unit_price = master_record.unit_price if master_record else 5.00  # Default price if no master record
            
            # Create Total Profile as a component with proper pricing
            self._create_accessory_component(
                'profiles', 'Total Profile', 
                int(self.total_profile), 'meters', unit_price
            )
    
    @api.depends('clamps_component_ids', 'clamps_component_ids.size_specification', 'clamps_component_ids.nos')
    def _compute_clamps_size_summary(self):
        """Compute a summary of clamp sizes and quantities"""
        for record in self:
            if not record.clamps_component_ids:
                record.clamps_size_summary = ""
                continue
            
            # Group clamps by size
            size_groups = {}
            for component in record.clamps_component_ids:
                size = component.size_specification or 'Unknown'
                if size not in size_groups:
                    size_groups[size] = 0
                size_groups[size] += component.nos
            
            # Create summary text
            if size_groups:
                summary_parts = []
                for size in sorted(size_groups.keys()):
                    summary_parts.append(f"{size}: {size_groups[size]} pcs")
                record.clamps_size_summary = " | ".join(summary_parts)
            else:
                record.clamps_size_summary = "No clamps configured"
    # ==================== OVERRIDE GRAND TOTAL ====================
    
    @api.depends('total_asc_cost', 'total_frame_cost', 'total_truss_cost', 
                 'total_lower_cost', 'total_accessories_cost')
    def _compute_section_totals(self):
        # Call parent method first
        super()._compute_section_totals()
        # Then add accessories to grand total
        for record in self:
            record.grand_total_cost += record.total_accessories_cost
    
    # ==================== CALCULATION METHODS ====================
    @api.constrains('enable_rollup_connectors', 'no_of_curtains')
    def _check_rollup_connectors(self):
        for record in self:
            if record.enable_rollup_connectors and record.no_of_curtains <= 0:
                raise ValidationError(_('Number of curtains must be greater than 0 when Roll Up Connectors are enabled.'))
        
    
    
    def action_calculate_process(self):
        """Override to include accessories calculation"""
        # Call parent method first
        result = super().action_calculate_process()
        
        # Then calculate accessories
        for record in self:
            try:
                record._calculate_all_accessories()
            except Exception as e:
                _logger.error(f"Error calculating accessories: {e}")
        
        return result
    
    def _calculate_all_accessories(self):
        """Calculate all accessories components"""
        try:
            # Save current accessories selections
            saved_accessories = self._save_accessories_selections()
            
            # Clear existing accessories
            self._clear_accessories_components()
            
            # Calculate each accessory type
            self._calculate_gutter_brackets()
            self._calculate_zigzag_wire()
            self._calculate_column_brackets()
            self._calculate_rollup_connectors()
            self._create_total_profile_component()
            self._calculate_foundation_rods()
            self.clamps_component_ids.unlink()
            self._calculate_advanced_clamps()
            # Restore selections
            self._restore_accessories_selections(saved_accessories)
            
        except Exception as e:
            _logger.error(f"Error in accessories calculation: {e}")
            raise
    
    def _clear_accessories_components(self):
        """Clear all existing accessories components"""
        if self.accessories_component_ids:
            self.accessories_component_ids.unlink()
    
    def _calculate_gutter_brackets(self):
        """Calculate gutter bracket components"""
        if self.gutter_bracket_type == 'arch':
            if self.last_span_gutter:
                # Gutter Arch Bracket HDGI 5.0 MM
                qty = (self.no_of_spans + 1) * (self.no_of_bays + 1)
                self._create_accessory_component(
                    'brackets', 'Gutter Arch Bracket HDGI 5.0 MM', qty, '5.0 MM'
                )
            else:
                # Main brackets
                qty_main = (self.no_of_spans - 1) * (self.no_of_bays + 1)
                self._create_accessory_component(
                    'brackets', 'Gutter Arch Bracket HDGI 5.0 MM', qty_main, '5.0 MM'
                )
                # Half brackets
                qty_half = self.no_of_bays + 1
                self._create_accessory_component(
                    'brackets', 'Gutter Arch Bracket HDGI Half Left', qty_half, 'Half'
                )
                self._create_accessory_component(
                    'brackets', 'Gutter Arch Bracket HDGI Half Right', qty_half, 'Half'
                )
        
        elif self.gutter_bracket_type == 'f_bracket':
            # F Bracket Big
            big_arch_count = self._get_big_arch_count()
            self._create_accessory_component(
                'brackets', 'F Bracket Big', big_arch_count, 'Big'
            )
            # F Bracket Small
            small_arch_count = self._get_small_arch_count()
            self._create_accessory_component(
                'brackets', 'F Bracket Small', small_arch_count, 'Small'
            )
    
    def _calculate_zigzag_wire(self):
        """Calculate zigzag wire components using total profile"""
        if self.enable_zigzag_wire:
            # Get total profile from computed field
            total_profile = self.total_profile
            
            # If total_profile is 0, try to calculate it
            if total_profile <= 0:
                total_profile = self._calculate_total_profile()
            
            # Wire length needed equals total profile length
            wire_length_needed = total_profile
            
            if wire_length_needed > 0:
                self._create_accessory_component(
                    'wires_connectors', f'Zigzag Wire {self.zigzag_wire_size}', 
                    int(wire_length_needed), self.zigzag_wire_size
                )
    
    def _calculate_column_brackets(self):
        """Calculate column bracket components"""
        middle_columns_count = self._get_middle_columns_count()
        
        if middle_columns_count <= 0:
            return
        
        if self.column_bracket_type == 'l_bracket':
            qty = middle_columns_count * 2
            self._create_accessory_component(
                'brackets', 'L Bracket', qty, 'Standard'
            )
        
        elif self.column_bracket_type == 'clamps':
            # Auto-detect pipe size from Middle Columns component
            pipe_size = self._get_middle_column_pipe_size()
            clamp_component = self._create_accessory_component(
                'clamps', 'Clamps', middle_columns_count, pipe_size
            )
            # Set auto-detected size for manual override capability
            if clamp_component:
                clamp_component.auto_detected_size = pipe_size
    
    def _calculate_rollup_connectors(self):
        """Calculate roll up connector components"""
        if self.enable_rollup_connectors and self.no_of_curtains > 0:
            # Roll Up Connector Smooth
            self._create_accessory_component(
                'wires_connectors', 'Roll Up Connector Smooth', 
                self.no_of_curtains, 'Standard'
            )
            # Roll Up Connector Handle
            self._create_accessory_component(
                'wires_connectors', 'Roll Up Connector Handle', 
                self.no_of_curtains, 'Standard'
            )
    
    # ==================== HELPER METHODS ====================
    
    def _create_accessory_component(self, section, name, nos, size_spec, custom_unit_price=None):
        """Create an accessory component - Updated to accept custom unit price"""
        try:
            # Skip if quantity is 0
            if nos <= 0:
                return None
                
            # Use custom unit price if provided, otherwise get from master data
            if custom_unit_price is not None:
                unit_price = custom_unit_price
            else:
                # Get default pricing from master data
                master_record = self.env['accessories.master'].search([
                    ('name', '=', name),
                    ('category', '=', section),
                    ('active', '=', True)
                ], limit=1)
                unit_price = master_record.unit_price if master_record else 0.0
            
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
            
            # Add master record if found
            if custom_unit_price is None:  # Only add master_id if not using custom pricing
                master_record = self.env['accessories.master'].search([
                    ('name', '=', name),
                    ('category', '=', section),
                    ('active', '=', True)
                ], limit=1)
                if master_record:
                    vals['accessories_master_id'] = master_record.id
            
            component = self.env['accessories.component.line'].create(vals)
            
            # For clamps, set auto-detected size
            if 'Clamps' in name and section == 'clamps':
                component.auto_detected_size = size_spec
                
            return component
            
        except Exception as e:
            _logger.error(f"Error creating accessory component {name}: {e}")
            return None
    
    def _get_big_arch_count(self):
        """Get count of big arches"""
        big_arch_component = self.truss_component_ids.filtered(lambda c: c.name == 'Big Arch')
        return big_arch_component.nos if big_arch_component else 0
    
    def _get_small_arch_count(self):
        """Get count of small arches"""
        small_arch_component = self.truss_component_ids.filtered(lambda c: c.name == 'Small Arch')
        return small_arch_component.nos if small_arch_component else 0
    
    def _get_middle_columns_count(self):
        """Get count of middle columns"""
        # Check multiple possible names for middle columns
        middle_columns = self.frame_component_ids.filtered(
            lambda c: c.name in ['Middle Columns', 'Quadruple Columns']
        )
        if middle_columns:
            return middle_columns[0].nos
        
        # Fallback: calculate based on structure if no components found
        # This happens when accessories are calculated before main components
        if hasattr(self, 'no_column_big_frame') and self.no_column_big_frame:
            if self.no_column_big_frame == '1':
                return self.no_anchor_frame_lines * self.no_of_spans
            elif self.no_column_big_frame in ['2', '3']:
                return self.no_anchor_frame_lines * self.no_of_spans * 2
        
        return 0
    
    def _get_middle_column_pipe_size(self):
        """Get pipe size for middle columns"""
        middle_columns = self.frame_component_ids.filtered(
            lambda c: c.name in ['Middle Columns', 'Quadruple Columns']
        )
        if middle_columns and middle_columns[0].pipe_id:
            pipe_size = middle_columns[0].pipe_id.pipe_size
            return f"{pipe_size.size_in_mm}mm" if pipe_size else "Unknown"
        return "Unknown"
        
        
        
    def _calculate_foundation_rods(self):
        """Calculate foundation rods: (No of Foundations * 2) + (No of ASC Pipes * 2)"""
        if self.enable_foundation_rods:
            foundations_count = self._get_foundations_count()
            asc_pipes_count = self._get_asc_pipes_count()
            
            total_rods = (foundations_count * self.foundation_rods_per_foundation) + (asc_pipes_count * self.foundation_rods_per_asc)
            
            if total_rods > 0:
                self._create_accessory_component(
                    'foundation', 
                    'Foundation Rods', 
                    total_rods, 
                    'Standard'
                )

    def _get_foundations_count(self):
        """Get total number of foundations"""
        total_foundations = 0
        debug_info = []
        
        # Collect debug info
        debug_info.append(f"Total frame components: {len(self.frame_component_ids)}")
        
        for component in self.frame_component_ids:
            debug_info.append(f"Frame: '{component.name}' - Nos: {component.nos}")
        
        foundation_components = self.frame_component_ids.filtered(
            lambda c: 'Foundations' in c.name and 'Columns' in c.name
        )
        
        debug_info.append(f"Found {len(foundation_components)} foundation components")
        
        for component in foundation_components:
            debug_info.append(f"Foundation: '{component.name}' - Nos: {component.nos}")
            total_foundations += component.nos
        
        debug_info.append(f"TOTAL: {total_foundations}")
        
        # Use standard Odoo notification
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'title': 'Foundation Count Debug',
                'message': "\n".join(debug_info),
                'type': 'info'
            }
        )
        
        return total_foundations

    def _get_asc_pipes_count(self):
        """Get total number of ASC pipes"""
        total_asc_pipes = 0
        
        # Get all ASC pipe components
        asc_components = self.asc_component_ids.filtered(
            lambda c: 'ASC Pipes' in c.name
        )
        
        for component in asc_components:
            total_asc_pipes += component.nos
        
        return total_asc_pipes
            
     
    def _calculate_advanced_clamps(self):
        """Calculate advanced clamp components based on type with size aggregation"""
        if self.clamp_type == 'none':
            return
            
        # Dictionary to accumulate clamps by type and size
        clamp_accumulator = {}
        
        if self.clamp_type == 'w_type':
            self._accumulate_w_type_clamps(clamp_accumulator)
        elif self.clamp_type == 'm_type':
            self._accumulate_m_type_clamps(clamp_accumulator)
        
        # Create components from accumulated data
        self._create_clamp_components_from_accumulator(clamp_accumulator)

    def _accumulate_w_type_clamps(self, accumulator):
        """Accumulate W Type clamp requirements by type and size"""
        
        # Get component counts and sizes
        bottom_chord_data = self._get_bottom_chord_data()
        bottom_chord_data['count'] = ceil(bottom_chord_data['count']  - (bottom_chord_data['afs_count']/2) )
        v_support_count = self._get_v_support_count()
        big_arch_data = self._get_big_arch_data()
        small_arch_data = self._get_small_arch_data()
        vent_support_big_arch = self._get_vent_support_big_arch_count()
        arch_support_straight_middle_data = self._get_arch_support_straight_middle_data()
        middle_column_data = self._get_middle_column_data()
        
        # 1. Bottom Chord Full Clamps
        if bottom_chord_data['count'] > 0 and bottom_chord_data['size']:
            qty = (bottom_chord_data['count'] * 3) + v_support_count
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', bottom_chord_data['size'], qty)
        
        # 2. Big Arch Full Clamps
        if big_arch_data['count'] > 0 and big_arch_data['size']:
            qty = (big_arch_data['count'] * 2) + vent_support_big_arch
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], qty)
        
        # 3. Small Arch Full Clamps
        if small_arch_data['count'] > 0 and small_arch_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_data['size'], small_arch_data['count'])
        
        # 4. Arch Support Straight Middle Clamps
        if arch_support_straight_middle_data['count'] > 0 and arch_support_straight_middle_data['size']:
            # Full Clamps
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                    arch_support_straight_middle_data['size'], 
                                    arch_support_straight_middle_data['count'])
            # Half Clamps
            self._add_to_clamp_accumulator(accumulator, 'Half Clamp', 
                                    arch_support_straight_middle_data['size'], 
                                    arch_support_straight_middle_data['count'])
        
        # 5. Middle Column Clamps
        if middle_column_data['count'] > 0 and middle_column_data['size']:
            # Full Clamps
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                    middle_column_data['size'], 
                                    middle_column_data['count'])
            # Half Clamps
            self._add_to_clamp_accumulator(accumulator, 'Half Clamp', 
                                    middle_column_data['size'], 
                                    middle_column_data['count'])
        
        # 6. Big Purlin Clamps - BOTH types
        if big_arch_data['size']:
            # First type (Full Clamp or L Joint) - for No of Spans * 2
            if self.big_purlin_clamp_type_first:
                qty_first = self.no_of_spans * 2
                if self.big_purlin_clamp_type_first == 'full_clamp':
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], qty_first)
                elif self.big_purlin_clamp_type_first == 'l_joint':
                    self._add_to_clamp_accumulator(accumulator, 'L Joint', big_arch_data['size'], qty_first)
            
            # Second type (Half Clamp or T Joint) - for remaining
            if self.big_purlin_clamp_type_second:
                qty_second = big_arch_data['count'] - (self.no_of_spans * 2)
                if qty_second > 0:
                    if self.big_purlin_clamp_type_second == 'half_clamp':
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', big_arch_data['size'], qty_second)
                    elif self.big_purlin_clamp_type_second == 't_joint':
                        self._add_to_clamp_accumulator(accumulator, 'T Joint', big_arch_data['size'], qty_second)

        # 7. Small Purlin Clamps - BOTH types
        if small_arch_data['size']:
            # First type (Full Clamp or L Joint) - for No of Spans * 2
            if self.small_purlin_clamp_type_first:
                qty_first = self.no_of_spans * 2
                if self.small_purlin_clamp_type_first == 'full_clamp':
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_data['size'], qty_first)
                elif self.small_purlin_clamp_type_first == 'l_joint':
                    self._add_to_clamp_accumulator(accumulator, 'L Joint', small_arch_data['size'], qty_first)
            
            # Second type (Half Clamp or T Joint) - for remaining
            if self.small_purlin_clamp_type_second:
                qty_second = small_arch_data['count'] - (self.no_of_spans * 2)
                if qty_second > 0:
                    if self.small_purlin_clamp_type_second == 'half_clamp':
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', small_arch_data['size'], qty_second)
                    elif self.small_purlin_clamp_type_second == 't_joint':
                        self._add_to_clamp_accumulator(accumulator, 'T Joint', small_arch_data['size'], qty_second)

    def _accumulate_m_type_clamps(self, accumulator):
        """Accumulate M Type clamp requirements by type and size"""
        
        # Get component counts and sizes
        bottom_chord_data = self._get_bottom_chord_data()
        bottom_chord_data['count'] = ceil(bottom_chord_data['count']  - (bottom_chord_data['afs_count']/2) )
        v_support_count = self._get_v_support_count()
        big_arch_data = self._get_big_arch_data()
        small_arch_data = self._get_small_arch_data()
        vent_support_big_arch = self._get_vent_support_big_arch_count()
        arch_support_straight_middle_data = self._get_arch_support_straight_middle_data()
        middle_column_data = self._get_middle_column_data()
        
        # 1. Bottom Chord Clamps (Single or Triple)
        if bottom_chord_data['count'] > 0 and bottom_chord_data['size']:
            if self.bottom_chord_clamp_type == 'single':
                qty = (bottom_chord_data['count'] * 3) + v_support_count
                #qty = 0
            else:  # triple
                qty = (bottom_chord_data['count'] * 5) + v_support_count
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', bottom_chord_data['size'], qty)
        
        # 2. Big Arch Full Clamps (same as W Type)
        if big_arch_data['count'] > 0 and big_arch_data['size']:
            qty = (big_arch_data['count'] * 2) + vent_support_big_arch
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], qty)
        
        # 3. Small Arch Full Clamps (same as W Type)
        if small_arch_data['count'] > 0 and small_arch_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_data['size'], small_arch_data['count'])
        
        # 4. Arch Support Straight Middle - Only Full Clamps for M Type
        if arch_support_straight_middle_data['count'] > 0 and arch_support_straight_middle_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                    arch_support_straight_middle_data['size'], 
                                    arch_support_straight_middle_data['count'])
        
        # 5. Middle Column - Only Full Clamps for M Type
        if middle_column_data['count'] > 0 and middle_column_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                    middle_column_data['size'], 
                                    middle_column_data['count'])
        
        

    def _add_to_clamp_accumulator(self, accumulator, clamp_type, size, quantity):
        """Add clamp quantity to accumulator, grouping by type and size"""
        if quantity <= 0:
            return
            
        key = (clamp_type, size)
        if key in accumulator:
            accumulator[key] += quantity
        else:
            accumulator[key] = quantity

    def _create_clamp_components_from_accumulator(self, accumulator):
        """Create clamp components from accumulated data"""
        for (clamp_type, size), quantity in accumulator.items():
            # Get pricing from master data
            master_record = self.env['accessories.master'].search([
                ('name', '=', clamp_type),
                ('category', '=', 'clamps'),
                ('size_specification', '=', size),
                ('active', '=', True)
            ], limit=1)
            
            unit_price = master_record.unit_price if master_record else 0.0
            
            # Create component with proper naming
            component_name = f"{clamp_type} - {size}"
            
            vals = {
                'green_master_id': self.id,
                'section': 'clamps',
                'name': component_name,
                'nos': int(quantity),
                'size_specification': size,
                'unit_price': unit_price,
                'is_calculated': True,
                'description': f"Auto-calculated {clamp_type} for {size} pipes",
            }
            
            if master_record:
                vals['accessories_master_id'] = master_record.id
            
            self.env['accessories.component.line'].create(vals)

    # Helper methods for clamp data
    def _get_bottom_chord_data(self):
        """Get bottom chord count and pipe size (counting only singular + male, not female)"""
        # Filter bottom chord but exclude Female and V Support
        bottom_chord_components = self.truss_component_ids.filtered(
            lambda c: 'Bottom Chord' in c.name 
            and 'Female' not in c.name 
            and 'V Support' not in c.name
        )
        
        data = {'count': 0, 'size': None}
        
        if bottom_chord_components:
            # Sum the quantities
            data['count'] = sum(bottom_chord_components.mapped('nos'))
            
            # Get pipe size from first component with a pipe
            for component in bottom_chord_components:
                if component.pipe_id and component.pipe_id.pipe_size:
                    data['size'] = f"{component.pipe_id.pipe_size.size_in_mm:.0f}mm"
                    break
                    
        anchor_frame_singular = self.truss_component_ids.filtered(
            lambda c: c.name == 'Bottom Chord Anchor Frame Singular'
        )
        
        if anchor_frame_singular:
            data['afs_count'] = anchor_frame_singular.nos
        
        return data

    def _get_v_support_count(self):
        """Get V support count"""
        v_support = self.truss_component_ids.filtered(
            lambda c: c.name == 'V Support Bottom Chord'
        )
        return v_support.nos if v_support else 0

    def _get_big_arch_data(self):
        """Get big arch count and pipe size"""
        big_arch = self.truss_component_ids.filtered(lambda c: c.name == 'Big Arch')
        
        data = {'count': 0, 'size': None}
        
        if big_arch:
            data['count'] = big_arch.nos
            if big_arch.pipe_id and big_arch.pipe_id.pipe_size:
                data['size'] = f"{big_arch.pipe_id.pipe_size.size_in_mm:.0f}mm"
        
        return data

    def _get_small_arch_data(self):
        """Get small arch count and pipe size"""
        small_arch = self.truss_component_ids.filtered(lambda c: c.name == 'Small Arch')
        
        data = {'count': 0, 'size': None}
        
        if small_arch:
            data['count'] = small_arch.nos
            if small_arch.pipe_id and small_arch.pipe_id.pipe_size:
                data['size'] = f"{small_arch.pipe_id.pipe_size.size_in_mm:.0f}mm"
        
        return data

    def _get_vent_support_big_arch_count(self):
        """Get vent support for big arch count"""
        vent_support = self.truss_component_ids.filtered(
            lambda c: c.name == 'Vent Support for Big Arch'
        )
        return vent_support.nos if vent_support else 0

    def _get_arch_support_straight_middle_data(self):
        """Get arch support straight middle count and pipe size"""
        arch_support = self.truss_component_ids.filtered(
            lambda c: c.name == 'Arch Support Straight Middle'
        )
        
        data = {'count': 0, 'size': None}
        
        if arch_support:
            data['count'] = arch_support.nos
            if arch_support.pipe_id and arch_support.pipe_id.pipe_size:
                data['size'] = f"{arch_support.pipe_id.pipe_size.size_in_mm:.0f}mm"
        
        return data

    def _get_middle_column_data(self):
        """Get middle column count and pipe size"""
        middle_columns = self.frame_component_ids.filtered(
            lambda c: c.name == 'Middle Columns'
        )
        
        data = {'count': 0, 'size': None}
        
        if middle_columns:
            data['count'] = middle_columns.nos
            if middle_columns.pipe_id and middle_columns.pipe_id.pipe_size:
                data['size'] = f"{middle_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        
        return data
        
    
            
        
        
        
        
    
    def _save_accessories_selections(self):
        """Save current accessories selections before recalculation"""
        saved_selections = {}
        
        for component in self.accessories_component_ids:
            key = f"{component.section}_{component.name}"
            saved_selections[key] = {
                'unit_price': component.unit_price,
                'size_override': component.size_override,
                'manual_size': component.manual_size,
                'notes': component.notes or '',
                'accessories_master_id': component.accessories_master_id.id if component.accessories_master_id else False,
            }
        
        return saved_selections
    
    def _restore_accessories_selections(self, saved_selections):
        """Restore accessories selections after recalculation"""
        if not saved_selections:
            return
        
        for component in self.accessories_component_ids:
            key = f"{component.section}_{component.name}"
            if key in saved_selections:
                selection_data = saved_selections[key]
                try:
                    component.write({
                        'unit_price': selection_data['unit_price'],
                        'size_override': selection_data['size_override'],
                        'manual_size': selection_data['manual_size'],
                        'notes': selection_data['notes'],
                        'accessories_master_id': selection_data['accessories_master_id'],
                    })
                except Exception as e:
                    _logger.error(f"Failed to restore accessory selection for {component.name}: {e}")
    
    # ==================== ACTION METHODS ====================
    
    def action_calculate_accessories(self):
        """Manual accessories calculation button action"""
        for record in self:
            try:
                record._calculate_all_accessories()
                
                message = f'''ACCESSORIES CALCULATION COMPLETED:

🔧 Brackets: {record.total_brackets_cost:.2f} 
🔗 Wires & Connectors: {record.total_wires_connectors_cost:.2f}  
🛠️ Clamps: {record.total_clamps_cost:.2f}

📊 TOTAL ACCESSORIES: {record.total_accessories_cost:.2f}
💰 NEW GRAND TOTAL: {record.grand_total_cost:.2f}

Components generated: {len(record.accessories_component_ids)}'''
                
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
    
    def action_calculate_profiles(self):
        """Calculate and display profile breakdown"""
        for record in self:
            try:
                # Force recalculation
                record._compute_all_profiles()
                
                message = f'''PROFILE CALCULATION BREAKDOWN:

🏗️ Profiles For Arch: {record.profiles_for_arch:.2f}m
📏 Profile For Purlin: {record.profile_for_purlin:.2f}m  
⬇️ Profile for Bottom: {record.profile_for_bottom:.2f}m
📐 Side Profile: {record.side_profile:.2f}m
🚪 Door Profile: {record.door_profile:.2f}m

📊 TOTAL PROFILE: {record.total_profile:.2f}m

Formula Details:
• Profiles For Arch = {record.no_of_spans} × {ceil((record.span_length / 20) + 1)} × ({record.small_arch_length} + {record.big_arch_length} + vent lengths)
• Profile For Purlin = Big Arch Purlin + Small Arch Purlin + Gutter calculations + Gable Purlin
• Profile for Bottom = {record.span_length} × 2 = {record.profile_for_bottom:.2f}m
• Side Profile = Border Purlins + 8 × {'ASC max length' if record.is_side_coridoors else 'Column height'}
• Door Profile = Sum of all door component lengths'''
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Profile Calculation Complete',
                        'message': message,
                        'type': 'success',
                        'sticky': True,
                    }
                }
                
            except Exception as e:
                _logger.error(f"Error in profile calculation: {e}")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Profile Calculation Error',
                        'message': f'Error occurred: {str(e)}',
                        'type': 'danger',
                    }
                }
    
    def action_accessories_summary(self):
        """Show accessories calculation summary"""
        accessories_count = len(self.accessories_component_ids)
        
        sections_summary = []
        if self.profiles_component_ids:  # ADD THIS
            sections_summary.append(f"📏 Profiles: {len(self.profiles_component_ids)} items")

        if self.brackets_component_ids:
            sections_summary.append(f"🔧 Brackets: {len(self.brackets_component_ids)} items")
        if self.wires_connectors_component_ids:
            sections_summary.append(f"🔗 Wires & Connectors: {len(self.wires_connectors_component_ids)} items")
        if self.clamps_component_ids:
            sections_summary.append(f"🛠️ Clamps: {len(self.clamps_component_ids)} items")
        
        message = f'''ACCESSORIES SUMMARY:

Configuration:
• Gutter Bracket: {dict(self._fields['gutter_bracket_type'].selection)[self.gutter_bracket_type]}
• Zigzag Wire: {'Enabled (' + self.zigzag_wire_size + ')' if self.enable_zigzag_wire else 'Disabled'}
• Column Bracket: {dict(self._fields['column_bracket_type'].selection)[self.column_bracket_type]}
• Roll Up Connectors: {'Enabled' if self.enable_rollup_connectors else 'Disabled'}

Profile Summary:
📊 Total Profile: {self.total_profile:.2f}m

Components:
{chr(10).join(sections_summary) if sections_summary else 'No accessories components'}

Costs:
📏 Profiles: {self.total_profiles_cost:.2f} 
🔧 Brackets: {self.total_brackets_cost:.2f}
🔗 Wires & Connectors: {self.total_wires_connectors_cost:.2f}
🛠️ Clamps: {self.total_clamps_cost:.2f}

📊 TOTAL ACCESSORIES: {self.total_accessories_cost:.2f}
💰 GRAND TOTAL: {self.grand_total_cost:.2f}'''

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Accessories Summary',
                'message': message,
                'type': 'info',
                'sticky': True,
            }
        }
    
    # ==================== ONCHANGE METHODS ====================
    
    @api.onchange('gutter_bracket_type')
    def _onchange_gutter_bracket_type(self):
        if self.gutter_bracket_type == 'none':
            # Clear any gutter bracket related settings if needed
            pass
    
    @api.onchange('enable_zigzag_wire')
    def _onchange_enable_zigzag_wire(self):
        if not self.enable_zigzag_wire:
            # Reset zigzag wire size to default when disabled
            self.zigzag_wire_size = '1.4'
    
    @api.onchange('column_bracket_type')
    def _onchange_column_bracket_type(self):
        if self.column_bracket_type == 'none':
            # Clear any column bracket related settings if needed
            pass
    
    @api.onchange('enable_rollup_connectors')
    def _onchange_enable_rollup_connectors(self):
        if not self.enable_rollup_connectors:
            # Clear rollup connector settings if needed
            pass
            
    @api.onchange('clamp_type')
    def _onchange_clamp_type(self):
        if self.clamp_type == 'none':
            # Clear all clamp selections
            self.big_purlin_clamp_type_first = False
            self.big_purlin_clamp_type_second = False
            self.small_purlin_clamp_type_first = False
            self.small_purlin_clamp_type_second = False
            self.bottom_chord_clamp_type = 'single'
        elif self.clamp_type == 'w_type':
            # Set W Type defaults
            self.bottom_chord_clamp_type = 'single'  # Reset M Type field
            if not self.big_purlin_clamp_type_first:
                self.big_purlin_clamp_type_first = 'full_clamp'
            if not self.big_purlin_clamp_type_second:
                self.big_purlin_clamp_type_second = 'half_clamp'
            if not self.small_purlin_clamp_type_first:
                self.small_purlin_clamp_type_first = 'full_clamp'
            if not self.small_purlin_clamp_type_second:
                self.small_purlin_clamp_type_second = 'half_clamp'
        elif self.clamp_type == 'm_type':
            # Set M Type defaults
            if not self.bottom_chord_clamp_type:
                self.bottom_chord_clamp_type = 'single'
            if not self.big_purlin_clamp_type_first:
                self.big_purlin_clamp_type_first = False
            if not self.big_purlin_clamp_type_second:
                self.big_purlin_clamp_type_second = False
            if not self.small_purlin_clamp_type_first:
                self.small_purlin_clamp_type_first = False
            if not self.small_purlin_clamp_type_second:
                self.small_purlin_clamp_type_second = False
                
                
                
    def action_debug_clamps(self):
        """Debug action to show all clamp calculations"""
        debug_info = []
        
        # Get all data
        bottom_chord_data = self._get_bottom_chord_data()
        v_support_count = self._get_v_support_count()
        big_arch_data = self._get_big_arch_data()
        small_arch_data = self._get_small_arch_data()
        vent_support_big_arch = self._get_vent_support_big_arch_count()
        arch_support_straight_middle_data = self._get_arch_support_straight_middle_data()
        middle_column_data = self._get_middle_column_data()
        
        # Build debug message
        debug_info.append(f"=== CLAMP DEBUG INFO ===")
        debug_info.append(f"Clamp Type: {self.clamp_type}")
        debug_info.append("\n")
        
        # Component Counts
        debug_info.append("COMPONENT DATA:")
        debug_info.append("\n")
        debug_info.append(f"• Bottom Chord: Count={bottom_chord_data['count']}, Size={bottom_chord_data['size']}")
        debug_info.append("\n")
        debug_info.append(f"• V Support Count: {v_support_count}")
        debug_info.append(f"• Big Arch: Count={big_arch_data['count']}, Size={big_arch_data['size']}")
        debug_info.append(f"• Small Arch: Count={small_arch_data['count']}, Size={small_arch_data['size']}")
        debug_info.append(f"• Vent Support Big Arch: {vent_support_big_arch}")
        debug_info.append(f"• Arch Support Straight Middle: Count={arch_support_straight_middle_data['count']}, Size={arch_support_straight_middle_data['size']}")
        debug_info.append(f"• Middle Columns: Count={middle_column_data['count']}, Size={middle_column_data['size']}")
        debug_info.append(f"• No of Spans: {self.no_of_spans}")
        debug_info.append("\n")
        
        # Calculations based on type
        if self.clamp_type == 'w_type':
            debug_info.append("W TYPE CALCULATIONS:")
            
            # 1. Bottom Chord
            if bottom_chord_data['count'] > 0:
                qty = (bottom_chord_data['count'] * 3) + v_support_count
                debug_info.append(f"1. Bottom Chord Full Clamps: ({bottom_chord_data['count']} × 3) + {v_support_count} = {qty}")
            
            # 2. Big Arch
            if big_arch_data['count'] > 0:
                qty = (big_arch_data['count'] * 2) + vent_support_big_arch
                debug_info.append(f"2. Big Arch Full Clamps: ({big_arch_data['count']} × 2) + {vent_support_big_arch} = {qty}")
            
            # 3. Small Arch
            if small_arch_data['count'] > 0:
                debug_info.append(f"3. Small Arch Full Clamps: {small_arch_data['count']}")
            
            # 4. Arch Support Straight Middle
            if arch_support_straight_middle_data['count'] > 0:
                debug_info.append(f"4. Arch Support Straight Middle:")
                debug_info.append(f"   - Full Clamps: {arch_support_straight_middle_data['count']}")
                debug_info.append(f"   - Half Clamps: {arch_support_straight_middle_data['count']}")
            
            # 5. Middle Column
            if middle_column_data['count'] > 0:
                debug_info.append(f"5. Middle Column:")
                debug_info.append(f"   - Full Clamps: {middle_column_data['count']}")
                debug_info.append(f"   - Half Clamps: {middle_column_data['count']}")
            
            # 6. Big Purlin
            debug_info.append(f"6. Big Purlin Clamps:")
            debug_info.append(f"   - First Type ({self.big_purlin_clamp_type_first}): {self.no_of_spans} × 2 = {self.no_of_spans * 2}")
            remaining = big_arch_data['count'] - (self.no_of_spans * 2)
            debug_info.append(f"   - Second Type ({self.big_purlin_clamp_type_second}): {big_arch_data['count']} - {self.no_of_spans * 2} = {remaining}")
            
            # 7. Small Purlin
            debug_info.append(f"7. Small Purlin Clamps:")
            debug_info.append(f"   - First Type ({self.small_purlin_clamp_type_first}): {self.no_of_spans} × 2 = {self.no_of_spans * 2}")
            remaining = small_arch_data['count'] - (self.no_of_spans * 2)
            debug_info.append(f"   - Second Type ({self.small_purlin_clamp_type_second}): {small_arch_data['count']} - {self.no_of_spans * 2} = {remaining}")
            
        elif self.clamp_type == 'm_type':
            debug_info.append("M TYPE CALCULATIONS:")
            
            # 1. Bottom Chord
            if bottom_chord_data['count'] > 0:
                if self.bottom_chord_clamp_type == 'single':
                    qty = (bottom_chord_data['count'] * 3) + v_support_count
                    debug_info.append(f"1. Bottom Chord (Single): ({bottom_chord_data['count']} × 3) + {v_support_count} = {qty}")
                else:
                    qty = (bottom_chord_data['count'] * 5) + v_support_count
                    debug_info.append(f"1. Bottom Chord (Triple): ({bottom_chord_data['count']} × 5) + {v_support_count} = {qty}")
            
            # 2. Big Arch
            if big_arch_data['count'] > 0:
                qty = (big_arch_data['count'] * 2) + vent_support_big_arch
                debug_info.append(f"2. Big Arch Full Clamps: ({big_arch_data['count']} × 2) + {vent_support_big_arch} = {qty}")
            
            # 3. Small Arch
            if small_arch_data['count'] > 0:
                debug_info.append(f"3. Small Arch Full Clamps: {small_arch_data['count']}")
            
            # 4. Arch Support Straight Middle (Only Full)
            if arch_support_straight_middle_data['count'] > 0:
                debug_info.append(f"4. Arch Support Straight Middle Full Clamps: {arch_support_straight_middle_data['count']}")
            
            # 5. Middle Column (Only Full)
            if middle_column_data['count'] > 0:
                debug_info.append(f"5. Middle Column Full Clamps: {middle_column_data['count']}")
        
        # Show as notification
        message = "\n".join(debug_info)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '🔍 Clamp Calculations Debug',
                'message': message,
                'type': 'info',
                'sticky': True,
            }
        }
        
    def action_debug_bottom_chord(self):
        """Debug action to show all bottom chord component details"""
        debug_info = []
        
        # Get all bottom chord components
        bottom_chord_components = self.truss_component_ids.filtered(
            lambda c: 'Bottom Chord' in c.name
        )
        
        debug_info.append("=== BOTTOM CHORD COMPONENTS DEBUG ===")
        debug_info.append(f"Total Bottom Chord Components Found: {len(bottom_chord_components)}")
        debug_info.append("")
        
        if bottom_chord_components:
            total_count = 0
            
            for idx, component in enumerate(bottom_chord_components, 1):
                debug_info.append(f"Component #{idx}:")
                debug_info.append(f"  Name: {component.name}")
                debug_info.append(f"  Nos: {component.nos}")
                debug_info.append(f"  Length: {component.length}")
                debug_info.append(f"  Total Length: {component.total_length}")
                
                # Pipe details
                if component.pipe_id:
                    debug_info.append(f"  Pipe ID: {component.pipe_id.id}")
                    debug_info.append(f"  Pipe Type: {component.pipe_id.name.name if component.pipe_id.name else 'N/A'}")
                    if component.pipe_id.pipe_size:
                        debug_info.append(f"  Pipe Size: {component.pipe_id.pipe_size.size_in_mm}mm")
                    else:
                        debug_info.append(f"  Pipe Size: Not Set")
                    if component.pipe_id.wall_thickness:
                        debug_info.append(f"  Wall Thickness: {component.pipe_id.wall_thickness.thickness_in_mm}mm")
                    else:
                        debug_info.append(f"  Wall Thickness: Not Set")
                else:
                    debug_info.append(f"  Pipe: NOT ASSIGNED")
                
                debug_info.append("")
                total_count += component.nos
            
            debug_info.append(f"=== SUMMARY ===")
            debug_info.append(f"Total Quantity (sum of all nos): {total_count}")
            
            # Check if all have same pipe size
            pipe_sizes = []
            for comp in bottom_chord_components:
                if comp.pipe_id and comp.pipe_id.pipe_size:
                    pipe_sizes.append(f"{comp.pipe_id.pipe_size.size_in_mm:.0f}mm")
            
            unique_sizes = list(set(pipe_sizes))
            if unique_sizes:
                if len(unique_sizes) == 1:
                    debug_info.append(f"All components use same pipe size: {unique_sizes[0]}")
                else:
                    debug_info.append(f"WARNING: Different pipe sizes found: {', '.join(unique_sizes)}")
            else:
                debug_info.append("WARNING: No pipe sizes assigned")
                
        else:
            debug_info.append("NO BOTTOM CHORD COMPONENTS FOUND!")
            debug_info.append("")
            debug_info.append("Available Truss Components:")
            for comp in self.truss_component_ids:
                debug_info.append(f"  - {comp.name}")
        
        message = "\n".join(debug_info)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '🔍 Bottom Chord Components Debug',
                'message': message,
                'type': 'info',
                'sticky': True,
            }
        }