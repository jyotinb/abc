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
    
    # Border Purlin Clamps Summary
    border_purlin_clamps_summary = fields.Text(
        string='Border Purlin Clamps Summary',
        compute='_compute_border_purlin_clamps_summary',
        store=False
    )
    
    # Bay Side Clamp Required field
    bay_side_clamp_required = fields.Boolean(
        string='Bay Side Clamp Required',
        compute='_compute_bay_side_clamp_required',
        store=False
    )
    
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
                 'clamps_component_ids.total_cost', 'foundation_component_ids.total_cost', 
                 'profiles_component_ids.total_cost')
    def _compute_accessories_totals(self):
        for record in self:
            record.total_brackets_cost = sum(record.brackets_component_ids.mapped('total_cost'))
            record.total_wires_connectors_cost = sum(record.wires_connectors_component_ids.mapped('total_cost'))
            record.total_clamps_cost = sum(record.clamps_component_ids.mapped('total_cost'))
            record.total_foundation_cost = sum(record.foundation_component_ids.mapped('total_cost'))
            record.total_profiles_cost = sum(record.profiles_component_ids.mapped('total_cost'))
            record.total_accessories_cost = (record.total_brackets_cost + 
                                           record.total_wires_connectors_cost + 
                                           record.total_clamps_cost +
                                           record.total_foundation_cost +
                                           record.total_profiles_cost)
    
    @api.depends('clamps_component_ids', 'bay_side_border_purlin', 'span_side_border_purlin')
    def _compute_border_purlin_clamps_summary(self):
        """Compute summary of border purlin clamps"""
        for record in self:
            if int(record.bay_side_border_purlin) == 0 and int(record.span_side_border_purlin) == 0:
                record.border_purlin_clamps_summary = ""
                continue
            
            summary_parts = []
            
            if int(record.bay_side_border_purlin) > 0:
                summary_parts.append(f"Bay Side Border: {record.bay_side_border_purlin}")
            
            if int(record.span_side_border_purlin) > 0:
                summary_parts.append(f"Span Side Border: {record.span_side_border_purlin}")
            
            if record.no_anchor_frame_lines > 0:
                summary_parts.append(f"Anchor Frames: {record.no_anchor_frame_lines}")
            
            record.border_purlin_clamps_summary = " | ".join(summary_parts) if summary_parts else "No border purlins"
    
    @api.depends('width_front_bay_coridoor', 'width_back_bay_coridoor', 'bay_side_border_purlin')
    def _compute_bay_side_clamp_required(self):
        """Compute if bay side clamps are required based on ASC configuration"""
        for record in self:
            has_bay_asc = record.width_front_bay_coridoor > 0 or record.width_back_bay_coridoor > 0
            has_bay_border = int(record.bay_side_border_purlin) > 0
            record.bay_side_clamp_required = has_bay_asc and has_bay_border
    
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
            
            vent_big_length = 0
            vent_small_length = 0
            
            if hasattr(self, 'length_vent_big_arch_support') and self.length_vent_big_arch_support:
                vent_big_length = self.length_vent_big_arch_support.length_value
            
            if hasattr(self, 'length_vent_small_arch_support') and self.length_vent_small_arch_support:
                vent_small_length = self.length_vent_small_arch_support.length_value
            
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
            
            big_arch_purlin_component = self.truss_component_ids.filtered(lambda c: c.name == 'Big Arch Purlin')
            if big_arch_purlin_component:
                total_purlin_profile += big_arch_purlin_component.total_length
            
            small_arch_purlin_component = self.truss_component_ids.filtered(lambda c: c.name == 'Small Arch Purlin')
            if small_arch_purlin_component:
                total_purlin_profile += small_arch_purlin_component.total_length
            
            if self.gutter_type == 'continuous':
                gutter_purlin_component = self.lower_component_ids.filtered(lambda c: c.name == 'Gutter Purlin')
                if gutter_purlin_component:
                    total_purlin_profile += gutter_purlin_component.total_length
                    
            elif self.gutter_type == 'ippf':
                gutter_ippf_component = self.lower_component_ids.filtered(lambda c: c.name == 'Gutter IPPF Full')
                if gutter_ippf_component:
                    total_purlin_profile += gutter_ippf_component.total_length * 2
            
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
            profile_for_bottom = self.span_length * 2
            return profile_for_bottom
            
        except Exception as e:
            _logger.error(f"Error calculating profile for bottom: {e}")
            return 0

    def _calculate_side_profile(self):
        """Calculate Side Profile"""
        try:
            side_profile = 0
            
            bay_border_component = self.truss_component_ids.filtered(lambda c: c.name == 'Bay Side Border Purlin')
            if bay_border_component:
                side_profile += bay_border_component.total_length
            
            span_border_component = self.truss_component_ids.filtered(lambda c: c.name == 'Span Side Border Purlin')
            if span_border_component:
                side_profile += span_border_component.total_length
            
            multiplier_length = 0
            
            if self.is_side_coridoors:
                asc_lengths = []
                
                asc_component_names = [
                    'Front Span ASC Pipes', 'Back Span ASC Pipes',
                    'Front Bay ASC Pipes', 'Back Bay ASC Pipes'
                ]
                
                for asc_name in asc_component_names:
                    asc_component = self.asc_component_ids.filtered(lambda c: asc_name in c.name)
                    if asc_component:
                        asc_lengths.append(asc_component.length)
                
                multiplier_length = max(asc_lengths) if asc_lengths else self.column_height
            else:
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
            
            if hasattr(self, 'door_component_ids') and self.door_component_ids:
                door_profile += sum(self.door_component_ids.mapped('total_length'))
            
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
            master_record = self.env['accessories.master'].search([
                ('name', '=', 'Total Profile'),
                ('category', '=', 'profiles'),
                ('active', '=', True)
            ], limit=1)
            
            unit_price = master_record.unit_price if master_record else 5.00
            
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
            
            size_groups = {}
            for component in record.clamps_component_ids:
                size = component.size_specification or 'Unknown'
                if size not in size_groups:
                    size_groups[size] = 0
                size_groups[size] += component.nos
            
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
        super()._compute_section_totals()
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
        result = super().action_calculate_process()
        
        for record in self:
            try:
                record._calculate_all_accessories()
            except Exception as e:
                _logger.error(f"Error calculating accessories: {e}")
        
        return result
    
    def _calculate_all_accessories(self):
        """Calculate all accessories components"""
        try:
            saved_accessories = self._save_accessories_selections()
            
            self._clear_accessories_components()
            
            self._calculate_gutter_brackets()
            self._calculate_zigzag_wire()
            self._calculate_column_brackets()
            self._calculate_rollup_connectors()
            self._create_total_profile_component()
            self._calculate_foundation_rods()
            self.clamps_component_ids.unlink()
            self._calculate_advanced_clamps()
            
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
                qty = (self.no_of_spans + 1) * (self.no_of_bays + 1)
                self._create_accessory_component(
                    'brackets', 'Gutter Arch Bracket HDGI 5.0 MM', qty, '5.0 MM'
                )
            else:
                qty_main = (self.no_of_spans - 1) * (self.no_of_bays + 1)
                self._create_accessory_component(
                    'brackets', 'Gutter Arch Bracket HDGI 5.0 MM', qty_main, '5.0 MM'
                )
                qty_half = self.no_of_bays + 1
                self._create_accessory_component(
                    'brackets', 'Gutter Arch Bracket HDGI Half Left', qty_half, 'Half'
                )
                self._create_accessory_component(
                    'brackets', 'Gutter Arch Bracket HDGI Half Right', qty_half, 'Half'
                )
        
        elif self.gutter_bracket_type == 'f_bracket':
            big_arch_count = self._get_big_arch_count()
            self._create_accessory_component(
                'brackets', 'F Bracket Big', big_arch_count, 'Big'
            )
            small_arch_count = self._get_small_arch_count()
            self._create_accessory_component(
                'brackets', 'F Bracket Small', small_arch_count, 'Small'
            )
    
    def _calculate_zigzag_wire(self):
        """Calculate zigzag wire components using total profile"""
        if self.enable_zigzag_wire:
            total_profile = self.total_profile
            
            if total_profile <= 0:
                total_profile = self._calculate_total_profile()
            
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
            pipe_size = self._get_middle_column_pipe_size()
            clamp_component = self._create_accessory_component(
                'clamps', 'Clamps', middle_columns_count, pipe_size
            )
            if clamp_component:
                clamp_component.auto_detected_size = pipe_size
    
    def _calculate_rollup_connectors(self):
        """Calculate roll up connector components"""
        if self.enable_rollup_connectors and self.no_of_curtains > 0:
            self._create_accessory_component(
                'wires_connectors', 'Roll Up Connector Smooth', 
                self.no_of_curtains, 'Standard'
            )
            self._create_accessory_component(
                'wires_connectors', 'Roll Up Connector Handle', 
                self.no_of_curtains, 'Standard'
            )
    
    def _calculate_foundation_rods(self):
        """Calculate foundation rods"""
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
    
    def _calculate_advanced_clamps(self):
        """Calculate advanced clamp components based on type with size aggregation"""
        if self.clamp_type == 'none' and not (self.is_side_coridoors and self.support_hockeys > 0):
            # Check if we still need to calculate for border purlins or arch middle purlins
            if (int(self.bay_side_border_purlin) <= 0 and 
                int(self.span_side_border_purlin) <= 0 and
                self.arch_middle_purlin_big_arch == '0' and 
                self.arch_middle_purlin_small_arch == '0'):
                return
            
        clamp_accumulator = {}
        
        if self.clamp_type == 'w_type':
            self._accumulate_w_type_clamps(clamp_accumulator)
        elif self.clamp_type == 'm_type':
            self._accumulate_m_type_clamps(clamp_accumulator)
        
        # Add ASC Support Clamps (only if ASC enabled and support_hockeys > 0)
        if self.is_side_coridoors and self.support_hockeys > 0:
            self._accumulate_asc_support_clamps(clamp_accumulator)
        
        # ADD BORDER PURLIN CLAMPS
        self._accumulate_border_purlin_clamps(clamp_accumulator)
        
        # NEW: ADD ARCH MIDDLE PURLIN CLAMPS
        self._accumulate_arch_middle_purlin_clamps(clamp_accumulator)
        
        self._create_clamp_components_from_accumulator(clamp_accumulator)

    def _accumulate_w_type_clamps(self, accumulator):
        """Accumulate W Type clamp requirements by type and size"""
        
        bottom_chord_data = self._get_bottom_chord_data()
        bottom_chord_data['count'] = ceil(bottom_chord_data['count'] - (bottom_chord_data.get('afs_count', 0)/2))
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
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                    arch_support_straight_middle_data['size'], 
                                    arch_support_straight_middle_data['count'])
            self._add_to_clamp_accumulator(accumulator, 'Half Clamp', 
                                    arch_support_straight_middle_data['size'], 
                                    arch_support_straight_middle_data['count'])
        
        # 5. Middle Column Clamps
        if middle_column_data['count'] > 0 and middle_column_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                    middle_column_data['size'], 
                                    middle_column_data['count'])
            self._add_to_clamp_accumulator(accumulator, 'Half Clamp', 
                                    middle_column_data['size'], 
                                    middle_column_data['count'])
        
        # 6. Big Purlin Clamps
        if big_arch_data['size']:
            if self.big_purlin_clamp_type_first:
                qty_first = self.no_of_spans * 2
                if self.big_purlin_clamp_type_first == 'full_clamp':
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], qty_first)
                elif self.big_purlin_clamp_type_first == 'l_joint':
                    self._add_to_clamp_accumulator(accumulator, 'L Joint', big_arch_data['size'], qty_first)
            
            if self.big_purlin_clamp_type_second:
                qty_second = big_arch_data['count'] - (self.no_of_spans * 2)
                if qty_second > 0:
                    if self.big_purlin_clamp_type_second == 'half_clamp':
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', big_arch_data['size'], qty_second)
                    elif self.big_purlin_clamp_type_second == 't_joint':
                        self._add_to_clamp_accumulator(accumulator, 'T Joint', big_arch_data['size'], qty_second)

        # 7. Small Purlin Clamps
        if small_arch_data['size']:
            if self.small_purlin_clamp_type_first:
                qty_first = self.no_of_spans * 2
                if self.small_purlin_clamp_type_first == 'full_clamp':
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_data['size'], qty_first)
                elif self.small_purlin_clamp_type_first == 'l_joint':
                    self._add_to_clamp_accumulator(accumulator, 'L Joint', small_arch_data['size'], qty_first)
            
            if self.small_purlin_clamp_type_second:
                qty_second = small_arch_data['count'] - (self.no_of_spans * 2)
                if qty_second > 0:
                    if self.small_purlin_clamp_type_second == 'half_clamp':
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', small_arch_data['size'], qty_second)
                    elif self.small_purlin_clamp_type_second == 't_joint':
                        self._add_to_clamp_accumulator(accumulator, 'T Joint', small_arch_data['size'], qty_second)

    def _accumulate_m_type_clamps(self, accumulator):
        """Accumulate M Type clamp requirements by type and size"""
        
        bottom_chord_data = self._get_bottom_chord_data()
        bottom_chord_data['count'] = ceil(bottom_chord_data['count'] - (bottom_chord_data.get('afs_count', 0)/2))
        v_support_count = self._get_v_support_count()
        big_arch_data = self._get_big_arch_data()
        small_arch_data = self._get_small_arch_data()
        vent_support_big_arch = self._get_vent_support_big_arch_count()
        arch_support_straight_middle_data = self._get_arch_support_straight_middle_data()
        middle_column_data = self._get_middle_column_data()
        
        # 1. Bottom Chord Clamps
        if bottom_chord_data['count'] > 0 and bottom_chord_data['size']:
            if self.bottom_chord_clamp_type == 'single':
                qty = (bottom_chord_data['count'] * 3) + v_support_count
            else:  # triple
                qty = (bottom_chord_data['count'] * 5) + v_support_count
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', bottom_chord_data['size'], qty)
        
        # 2. Big Arch Full Clamps
        if big_arch_data['count'] > 0 and big_arch_data['size']:
            qty = (big_arch_data['count'] * 2) + vent_support_big_arch
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], qty)
        
        # 3. Small Arch Full Clamps
        if small_arch_data['count'] > 0 and small_arch_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_data['size'], small_arch_data['count'])
        
        # 4. Arch Support Straight Middle
        if arch_support_straight_middle_data['count'] > 0 and arch_support_straight_middle_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                    arch_support_straight_middle_data['size'], 
                                    arch_support_straight_middle_data['count'])
        
        # 5. Middle Column
        if middle_column_data['count'] > 0 and middle_column_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                    middle_column_data['size'], 
                                    middle_column_data['count'])

    def _accumulate_asc_support_clamps(self, accumulator):
        """Calculate ASC Support Pipe Clamps"""
        
        # Type A: Direct ASC Pipe Clamps
        asc_support_count = self._get_asc_support_pipes_count()
        asc_pipe_size = self._get_asc_pipe_size()
        
        if asc_support_count > 0 and asc_pipe_size:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', asc_pipe_size, asc_support_count)
        
        # Type B: Column-based clamps
        column_clamps = self._calculate_asc_column_clamps()
        
        # Add thick column clamps
        if column_clamps['thick_count'] > 0:
            thick_size = self._get_thick_column_pipe_size()
            if thick_size:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, column_clamps['thick_count'])
        
        # Add middle column clamps  
        if column_clamps['middle_count'] > 0:
            middle_size = self._get_middle_column_pipe_size()
            if middle_size:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, column_clamps['middle_count'])
        
        # Add main column clamps
        if column_clamps['main_count'] > 0:
            main_size = self._get_main_column_pipe_size()
            if main_size:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, column_clamps['main_count'])

    def _calculate_asc_column_clamps(self):
        """Calculate column clamps based on thick column configuration"""
        
        thick_columns_to_consider = 0
        middle_columns_to_consider = 0
        
        # Get ASC presence flags
        has_front_span = self.width_front_span_coridoor > 0
        has_back_span = self.width_back_span_coridoor > 0
        has_front_bay = self.width_front_bay_coridoor > 0
        has_back_bay = self.width_back_bay_coridoor > 0
        
        big_columns_per_af = int(self.no_column_big_frame)
        
        if self.thick_column == '0':  # None case - no thick columns configured
            # Only middle columns from anchor frames are considered
            if has_front_span:
                middle_columns_to_consider += self.no_of_spans * big_columns_per_af
            if has_back_span:
                middle_columns_to_consider += self.no_of_spans * big_columns_per_af
                
        elif self.thick_column == '1':  # 4 Corners
            if has_front_span:
                thick_columns_to_consider += 2
                middle_columns_to_consider += self.no_of_spans * big_columns_per_af
            if has_back_span:
                thick_columns_to_consider += 2
                middle_columns_to_consider += self.no_of_spans * big_columns_per_af
            if has_front_bay:
                thick_columns_to_consider += 2
            if has_back_bay:
                thick_columns_to_consider += 2
                
        elif self.thick_column == '2':  # 2 Bay Side
            if has_front_span:
                thick_columns_to_consider += 2
                middle_columns_to_consider += self.no_of_spans * big_columns_per_af
            if has_back_span:
                thick_columns_to_consider += 2
                middle_columns_to_consider += self.no_of_spans * big_columns_per_af
            if has_front_bay:
                thick_columns_to_consider += self.no_of_bays + 1
            if has_back_bay:
                thick_columns_to_consider += self.no_of_bays + 1
                
        elif self.thick_column == '3':  # 2 Span Side
            if has_front_span:
                thick_columns_to_consider += self.no_of_spans + 1
                middle_columns_to_consider += self.no_of_spans * big_columns_per_af
            if has_back_span:
                thick_columns_to_consider += self.no_of_spans + 1
                middle_columns_to_consider += self.no_of_spans * big_columns_per_af
            if has_front_bay:
                thick_columns_to_consider += 2
            if has_back_bay:
                thick_columns_to_consider += 2
                
        elif self.thick_column == '4':  # 4 Side
            if has_front_span:
                thick_columns_to_consider += self.no_of_spans + 1
                middle_columns_to_consider += self.no_of_spans * big_columns_per_af
            if has_back_span:
                thick_columns_to_consider += self.no_of_spans + 1
                middle_columns_to_consider += self.no_of_spans * big_columns_per_af
            if has_front_bay:
                thick_columns_to_consider += self.no_of_bays + 1
            if has_back_bay:
                thick_columns_to_consider += self.no_of_bays + 1
        
        # Calculate final clamp counts
        thick_clamp_count = thick_columns_to_consider * self.support_hockeys
        middle_clamp_count = middle_columns_to_consider * self.support_hockeys
        
        # Main column clamps = Total ASC Support - (thick + middle)
        total_asc_support = self._get_asc_support_pipes_count()
        main_clamp_count = total_asc_support - (thick_clamp_count + middle_clamp_count)
        
        # Ensure main_clamp_count is not negative
        main_clamp_count = max(0, main_clamp_count)
        
        return {
            'thick_count': thick_clamp_count,
            'middle_count': middle_clamp_count,
            'main_count': main_clamp_count
        }
    
    # ==================== BORDER PURLIN CLAMP METHODS ====================
    
    def _accumulate_border_purlin_clamps(self, accumulator):
        """Main method to accumulate all border purlin clamps"""
        try:
            # Only calculate if border purlins are configured
            if int(self.bay_side_border_purlin) > 0:
                self._accumulate_bay_side_border_clamps(accumulator)
            
            if int(self.span_side_border_purlin) > 0:
                self._accumulate_span_side_border_clamps(accumulator)
                
                # Handle Anchor Frame Lines special cases
                if self.no_anchor_frame_lines >= 1:
                    self._accumulate_anchor_frame_clamps(accumulator)
                    
        except Exception as e:
            _logger.error(f"Error accumulating border purlin clamps: {e}")
    
    def _accumulate_bay_side_border_clamps(self, accumulator):
        """Calculate Bay Side Border Purlin Clamps"""
        try:
            bay_side_value = int(self.bay_side_border_purlin)
            if bay_side_value <= 0:
                return
            
            # Front Bay Clamps
            if self.width_front_bay_coridoor > 0:  # Has Front Bay ASC
                pipe_size = self._get_asc_pipe_size()
                hockey_count = self._get_front_bay_hockey_count()
                if pipe_size and hockey_count > 0:
                    # Half Clamps
                    half_qty = (hockey_count - 1) * bay_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', pipe_size, half_qty)
                    # Full Clamps
                    full_qty = 2 * bay_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', pipe_size, full_qty)
            else:  # No Front Bay ASC
                half_size, full_size = self._get_bay_side_pipe_sizes('front')
                if half_size and full_size:
                    # Half Clamps
                    half_qty = self.no_of_bays * bay_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', half_size, half_qty)
                    # Full Clamps
                    full_qty = 2 * bay_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', full_size, full_qty)
            
            # Back Bay Clamps
            if self.width_back_bay_coridoor > 0:  # Has Back Bay ASC
                pipe_size = self._get_asc_pipe_size()
                hockey_count = self._get_back_bay_hockey_count()
                if pipe_size and hockey_count > 0:
                    # Half Clamps
                    half_qty = (hockey_count - 1) * bay_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', pipe_size, half_qty)
                    # Full Clamps
                    full_qty = 2 * bay_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', pipe_size, full_qty)
            else:  # No Back Bay ASC
                half_size, full_size = self._get_bay_side_pipe_sizes('back')
                if half_size and full_size:
                    # Half Clamps
                    half_qty = self.no_of_bays * bay_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', half_size, half_qty)
                    # Full Clamps
                    full_qty = 2 * bay_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', full_size, full_qty)
                    
        except Exception as e:
            _logger.error(f"Error calculating bay side border clamps: {e}")
    
    def _accumulate_span_side_border_clamps(self, accumulator):
        """Calculate Span Side Border Purlin Clamps"""
        try:
            span_side_value = int(self.span_side_border_purlin)
            if span_side_value <= 0:
                return
            
            big_frame_multiplier = int(self.no_column_big_frame) + 1
            
            # Front Span Clamps
            if self.width_front_span_coridoor > 0:  # Has Front Span ASC
                pipe_size = self._get_asc_pipe_size()
                hockey_count = self._get_front_span_hockey_count()
                if pipe_size and hockey_count > 0:
                    # Half Clamps
                    half_qty = (hockey_count - 1) * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', pipe_size, half_qty)
                    # Full Clamps
                    full_qty = 2 * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', pipe_size, full_qty)
            else:  # No Front Span ASC
                half_size, full_size = self._get_span_side_pipe_sizes('front')
                if half_size and full_size:
                    # Half Clamps
                    half_qty = (self.no_of_spans * big_frame_multiplier) * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', half_size, half_qty)
                    # Full Clamps
                    full_qty = 2 * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', full_size, full_qty)
            
            # Back Span Clamps
            if self.width_back_span_coridoor > 0:  # Has Back Span ASC
                pipe_size = self._get_asc_pipe_size()
                hockey_count = self._get_back_span_hockey_count()
                if pipe_size and hockey_count > 0:
                    # Half Clamps
                    half_qty = (hockey_count - 1) * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', pipe_size, half_qty)
                    # Full Clamps
                    full_qty = 2 * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', pipe_size, full_qty)
            else:  # No Back Span ASC
                half_size, full_size = self._get_span_side_pipe_sizes('back')
                if half_size and full_size:
                    # Half Clamps
                    half_qty = (self.no_of_spans * big_frame_multiplier) * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', half_size, half_qty)
                    # Full Clamps
                    full_qty = 2 * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', full_size, full_qty)
                    
        except Exception as e:
            _logger.error(f"Error calculating span side border clamps: {e}")
    
    def _accumulate_anchor_frame_clamps(self, accumulator):
        """Handle Anchor Frame Lines special calculations"""
        try:
            span_side_value = int(self.span_side_border_purlin)
            if span_side_value <= 0 or self.no_anchor_frame_lines <= 0:
                return
            
            if self.no_anchor_frame_lines == 1:
                # Log notification
                _logger.info("Anchor Frame Lines = 1: ASC and Anchor Frame Lines considered at same line")
                
                # Check for any ASC presence
                has_front_asc = self.width_front_span_coridoor > 0
                has_back_asc = self.width_back_span_coridoor > 0
                
                if has_front_asc or has_back_asc:
                    pipe_size = self._get_asc_pipe_size()
                else:
                    pipe_size = self._get_big_column_pipe_size()
                
                if pipe_size:
                    half_qty = self.no_of_spans * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', pipe_size, half_qty)
                    
            elif self.no_anchor_frame_lines >= 2:
                # Front Span Anchor Frame
                if self.width_front_span_coridoor > 0:
                    pipe_size = self._get_asc_pipe_size()
                else:
                    pipe_size = self._get_big_column_pipe_size()
                
                if pipe_size:
                    half_qty = self.no_of_spans * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', pipe_size, half_qty)
                
                # Back Span Anchor Frame
                if self.width_back_span_coridoor > 0:
                    pipe_size = self._get_asc_pipe_size()
                else:
                    pipe_size = self._get_big_column_pipe_size()
                
                if pipe_size:
                    half_qty = self.no_of_spans * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', pipe_size, half_qty)
                    
        except Exception as e:
            _logger.error(f"Error calculating anchor frame clamps: {e}")
    
    # ==================== ARCH MIDDLE PURLIN CLAMP METHODS ====================
    
    def _accumulate_arch_middle_purlin_clamps(self, accumulator):
        """Accumulate Arch Middle Purlin clamp requirements"""
        
        # Big Arch Middle Purlin
        if self.arch_middle_purlin_big_arch != '0' and int(self.arch_middle_purlin_big_arch_pcs) > 0:
            self._accumulate_big_arch_middle_purlin(accumulator)
        
        # Small Arch Middle Purlin
        if self.arch_middle_purlin_small_arch != '0' and int(self.arch_middle_purlin_small_arch_pcs) > 0:
            self._accumulate_small_arch_middle_purlin(accumulator)

    def _accumulate_big_arch_middle_purlin(self, accumulator):
        """Accumulate Big Arch Middle Purlin clamps"""
        config_value = self.arch_middle_purlin_big_arch
        pcs_value = int(self.arch_middle_purlin_big_arch_pcs)
        
        # Get component count
        no_arch_middle_purlin_big_arch = 0
        arch_middle_purlin = self.lower_component_ids.filtered(
            lambda c: c.name == 'Arch Middle Purlin Big Arch'
        )
        if arch_middle_purlin:
            no_arch_middle_purlin_big_arch = arch_middle_purlin.nos
        
        # Get Big Arch pipe size
        big_arch_data = self._get_big_arch_data()
        big_arch_size = big_arch_data['size']
        
        if not big_arch_size or no_arch_middle_purlin_big_arch == 0:
            return
        
        # Calculate Full Clamps
        full_qty = 0
        
        if config_value == '1':  # 4 Corners
            full_qty = no_arch_middle_purlin_big_arch * 2
        elif config_value == '2':  # Front & Back
            full_qty = no_arch_middle_purlin_big_arch * 2
        elif config_value == '3':  # Both Sides
            full_qty = 4 * pcs_value
        elif config_value == '4':  # 4 Sides
            full_qty = ((((self.no_of_spans - 2) * 4) + 4) * pcs_value)
        elif config_value == '5':  # All
            full_qty = self.no_of_spans * 2
        
        if full_qty > 0:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_size, full_qty)
        
        # Calculate Half Clamps (only for specific configurations)
        half_qty = 0
        
        if config_value == '3':  # Both Sides
            half_qty = (no_arch_middle_purlin_big_arch * 2) - (4 * pcs_value)
        elif config_value == '4':  # 4 Sides
            half_qty = no_arch_middle_purlin_big_arch - (((((self.no_of_spans - 2) * 4) + 4) * pcs_value) / 2)
        elif config_value == '5':  # All
            half_qty = self.no_of_spans * (self.no_of_bays - 1)
        
        if half_qty > 0:
            self._add_to_clamp_accumulator(accumulator, 'Half Clamp', big_arch_size, half_qty)

    def _accumulate_small_arch_middle_purlin(self, accumulator):
        """Accumulate Small Arch Middle Purlin clamps"""
        config_value = self.arch_middle_purlin_small_arch
        pcs_value = int(self.arch_middle_purlin_small_arch_pcs)
        
        # Get component count
        no_arch_middle_purlin_small_arch = 0
        arch_middle_purlin = self.lower_component_ids.filtered(
            lambda c: c.name == 'Arch Middle Purlin Small Arch'
        )
        if arch_middle_purlin:
            no_arch_middle_purlin_small_arch = arch_middle_purlin.nos
        
        # Get Small Arch pipe size
        small_arch_data = self._get_small_arch_data()
        small_arch_size = small_arch_data['size']
        
        if not small_arch_size or no_arch_middle_purlin_small_arch == 0:
            return
        
        # Calculate Full Clamps
        full_qty = 0
        
        if config_value == '1':  # 4 Corners
            full_qty = no_arch_middle_purlin_small_arch * 2
        elif config_value == '2':  # Front & Back
            full_qty = no_arch_middle_purlin_small_arch * 2
        elif config_value == '3':  # Both Sides
            full_qty = 4 * pcs_value
        elif config_value == '4':  # 4 Sides
            full_qty = ((((self.no_of_spans - 2) * 4) + 4) * pcs_value)
        elif config_value == '5':  # All
            full_qty = self.no_of_spans * 2
        
        if full_qty > 0:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_size, full_qty)
        
        # Calculate Half Clamps (only for specific configurations)
        half_qty = 0
        
        if config_value == '3':  # Both Sides
            half_qty = (no_arch_middle_purlin_small_arch * 2) - (4 * pcs_value)
        elif config_value == '4':  # 4 Sides
            half_qty = no_arch_middle_purlin_small_arch - (((((self.no_of_spans - 2) * 4) + 4) * pcs_value) / 2)
        elif config_value == '5':  # All
            half_qty = self.no_of_spans * (self.no_of_bays - 1)
        
        if half_qty > 0:
            self._add_to_clamp_accumulator(accumulator, 'Half Clamp', small_arch_size, half_qty)
    
    # ==================== HELPER METHODS FOR BORDER PURLINS ====================
    
    def _get_bay_side_pipe_sizes(self, location='front'):
        """Determine pipe sizes for bay side based on thick column configuration"""
        try:
            thick_config = self.thick_column
            
            # For 4 Corners configuration
            if thick_config == '1':
                half_size = self._get_main_column_pipe_size()
                full_size = self._get_thick_column_pipe_size()
                
            # For Bay Side configurations (2 Bay Side or All 4 Side)
            elif thick_config in ['2', '4']:
                half_size = self._get_thick_column_pipe_size()
                full_size = self._get_thick_column_pipe_size()
                
            # No thick columns
            else:  # thick_config == '0'
                half_size = self._get_main_column_pipe_size()
                full_size = self._get_main_column_pipe_size()
            
            return half_size, full_size
            
        except Exception as e:
            _logger.error(f"Error determining bay side pipe sizes: {e}")
            return None, None
    
    def _get_span_side_pipe_sizes(self, location='front'):
        """Determine pipe sizes for span side based on thick column configuration"""
        try:
            thick_config = self.thick_column
            
            # For 4 Corners configuration
            if thick_config == '1':
                half_size = self._get_main_column_pipe_size()
                full_size = self._get_thick_column_pipe_size()
                
            # For Span Side configurations (2 Span Side or All 4 Side)
            elif thick_config in ['3', '4']:
                half_size = self._get_thick_column_pipe_size()
                full_size = self._get_thick_column_pipe_size()
                
            # No thick columns
            else:  # thick_config == '0'
                half_size = self._get_main_column_pipe_size()
                full_size = self._get_main_column_pipe_size()
            
            return half_size, full_size
            
        except Exception as e:
            _logger.error(f"Error determining span side pipe sizes: {e}")
            return None, None
    
    def _get_front_bay_hockey_count(self):
        """Calculate front bay hockey count"""
        try:
            if self.width_front_bay_coridoor > 0:
                return (self.span_length / self.bay_width) + 1
            return 0
        except Exception:
            return 0
    
    def _get_back_bay_hockey_count(self):
        """Calculate back bay hockey count"""
        try:
            if self.width_back_bay_coridoor > 0:
                return (self.span_length / self.bay_width) + 1
            return 0
        except Exception:
            return 0
    
    def _get_front_span_hockey_count(self):
        """Calculate front span hockey count"""
        try:
            if self.width_front_span_coridoor > 0:
                big_frame = int(self.no_column_big_frame) + 1
                return ((self.bay_length / self.span_width) * big_frame) + 1
            return 0
        except Exception:
            return 0
    
    def _get_back_span_hockey_count(self):
        """Calculate back span hockey count"""
        try:
            if self.width_back_span_coridoor > 0:
                big_frame = int(self.no_column_big_frame) + 1
                return ((self.bay_length / self.span_width) * big_frame) + 1
            return 0
        except Exception:
            return 0
    
    def _get_big_column_pipe_size(self):
        """Get big column pipe size from middle or quadruple columns"""
        try:
            # Check Middle Columns
            middle_columns = self.frame_component_ids.filtered(
                lambda c: c.name == 'Middle Columns'
            )
            if middle_columns and middle_columns.pipe_id and middle_columns.pipe_id.pipe_size:
                return f"{middle_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
            
            # Check Quadruple Columns
            quadruple_columns = self.frame_component_ids.filtered(
                lambda c: c.name == 'Quadruple Columns'
            )
            if quadruple_columns and quadruple_columns.pipe_id and quadruple_columns.pipe_id.pipe_size:
                return f"{quadruple_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
            
            # Fallback to main column
            return self._get_main_column_pipe_size()
            
        except Exception as e:
            _logger.error(f"Error getting big column pipe size: {e}")
            return None

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
            master_record = self.env['accessories.master'].search([
                ('name', '=', clamp_type),
                ('category', '=', 'clamps'),
                ('size_specification', '=', size),
                ('active', '=', True)
            ], limit=1)
            
            unit_price = master_record.unit_price if master_record else 0.0
            
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

    # ==================== HELPER METHODS ====================
    
    def _create_accessory_component(self, section, name, nos, size_spec, custom_unit_price=None):
        """Create an accessory component"""
        try:
            if nos <= 0:
                return None
                
            if custom_unit_price is not None:
                unit_price = custom_unit_price
            else:
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
            
            if custom_unit_price is None:
                master_record = self.env['accessories.master'].search([
                    ('name', '=', name),
                    ('category', '=', section),
                    ('active', '=', True)
                ], limit=1)
                if master_record:
                    vals['accessories_master_id'] = master_record.id
            
            component = self.env['accessories.component.line'].create(vals)
            
            if 'Clamps' in name and section == 'clamps':
                component.auto_detected_size = size_spec
                
            return component
            
        except Exception as e:
            _logger.error(f"Error creating accessory component {name}: {e}")
            return None
    
    # Helper methods for getting counts
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
        middle_columns = self.frame_component_ids.filtered(
            lambda c: c.name in ['Middle Columns', 'Quadruple Columns']
        )
        if middle_columns:
            return middle_columns[0].nos
        
        if hasattr(self, 'no_column_big_frame') and self.no_column_big_frame:
            if self.no_column_big_frame == '1':
                return self.no_anchor_frame_lines * self.no_of_spans
            elif self.no_column_big_frame in ['2', '3']:
                return self.no_anchor_frame_lines * self.no_of_spans * 2
        
        return 0
    
    def _get_foundations_count(self):
        """Get total number of foundations"""
        total_foundations = 0
        
        foundation_components = self.frame_component_ids.filtered(
            lambda c: 'Foundations' in c.name and 'Columns' in c.name
        )
        
        for component in foundation_components:
            total_foundations += component.nos
        
        return total_foundations

    def _get_asc_pipes_count(self):
        """Get total number of ASC pipes"""
        total_asc_pipes = 0
        
        asc_components = self.asc_component_ids.filtered(
            lambda c: 'ASC Pipes' in c.name
        )
        
        for component in asc_components:
            total_asc_pipes += component.nos
        
        return total_asc_pipes
    
    def _get_asc_support_pipes_count(self):
        """Get total count of ASC support pipes"""
        asc_support = self.asc_component_ids.filtered(
            lambda c: c.name == 'ASC Pipe Support'
        )
        return asc_support.nos if asc_support else 0
        
    def _get_asc_pipe_size(self):
        """Get pipe size from any ASC pipe component"""
        asc_pipes = self.asc_component_ids.filtered(
            lambda c: 'ASC Pipes' in c.name
        )
        if asc_pipes and asc_pipes[0].pipe_id and asc_pipes[0].pipe_id.pipe_size:
            return f"{asc_pipes[0].pipe_id.pipe_size.size_in_mm:.0f}mm"
        return None

    def _get_thick_column_pipe_size(self):
        """Get thick column pipe size"""
        thick_columns = self.frame_component_ids.filtered(
            lambda c: c.name == 'Thick Columns'
        )
        if thick_columns and thick_columns.pipe_id and thick_columns.pipe_id.pipe_size:
            return f"{thick_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return None

    def _get_main_column_pipe_size(self):
        """Get main column pipe size"""
        main_columns = self.frame_component_ids.filtered(
            lambda c: c.name == 'Main Columns'
        )
        if main_columns and main_columns.pipe_id and main_columns.pipe_id.pipe_size:
            return f"{main_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return None

    def _get_middle_column_pipe_size(self):
        """Get middle column pipe size - handles both Middle and Quadruple columns"""
        middle_columns = self.frame_component_ids.filtered(
            lambda c: c.name in ['Middle Columns', 'Quadruple Columns']
        )
        if middle_columns and middle_columns[0].pipe_id and middle_columns[0].pipe_id.pipe_size:
            return f"{middle_columns[0].pipe_id.pipe_size.size_in_mm:.0f}mm"
        return None
    
    # Helper methods for clamp data
    def _get_bottom_chord_data(self):
        """Get bottom chord count and pipe size"""
        bottom_chord_components = self.truss_component_ids.filtered(
            lambda c: 'Bottom Chord' in c.name 
            and 'Female' not in c.name 
            and 'V Support' not in c.name
        )
        
        data = {'count': 0, 'size': None, 'afs_count': 0}
        
        if bottom_chord_components:
            data['count'] = sum(bottom_chord_components.mapped('nos'))
            
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
                record._compute_all_profiles()
                
                message = f'''PROFILE CALCULATION BREAKDOWN:

🏗️ Profiles For Arch: {record.profiles_for_arch:.2f}m
📏 Profile For Purlin: {record.profile_for_purlin:.2f}m  
⬇️ Profile for Bottom: {record.profile_for_bottom:.2f}m
📐 Side Profile: {record.side_profile:.2f}m
🚪 Door Profile: {record.door_profile:.2f}m

📊 TOTAL PROFILE: {record.total_profile:.2f}m'''
                
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
        sections_summary = []
        if self.profiles_component_ids:
            sections_summary.append(f"📏 Profiles: {len(self.profiles_component_ids)} items")
        if self.brackets_component_ids:
            sections_summary.append(f"🔧 Brackets: {len(self.brackets_component_ids)} items")
        if self.wires_connectors_component_ids:
            sections_summary.append(f"🔗 Wires & Connectors: {len(self.wires_connectors_component_ids)} items")
        if self.clamps_component_ids:
            sections_summary.append(f"🛠️ Clamps: {len(self.clamps_component_ids)} items")
        
        message = f'''ACCESSORIES SUMMARY:

Configuration:
- Gutter Bracket: {dict(self._fields['gutter_bracket_type'].selection)[self.gutter_bracket_type]}
- Zigzag Wire: {'Enabled (' + self.zigzag_wire_size + ')' if self.enable_zigzag_wire else 'Disabled'}
- Column Bracket: {dict(self._fields['column_bracket_type'].selection)[self.column_bracket_type]}
- Roll Up Connectors: {'Enabled' if self.enable_rollup_connectors else 'Disabled'}

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
    
    def action_view_clamp_details(self):
        """Show detailed clamp calculation breakdown in tree view"""
        
        # Create wizard record with calculations
        wizard = self.env['clamp.calculation.detail'].create({
            'green_master_id': self.id,
        })
        
        # Calculate clamps
        wizard.calculate_clamps()
        
        # Return action to open the wizard
        return {
            'type': 'ir.actions.act_window',
            'name': 'Clamp Calculation Details',
            'res_model': 'clamp.calculation.detail',
            'res_id': wizard.id,
            'view_mode': 'form',
            'view_id': self.env.ref('green2_accessories_2.view_clamp_calculation_detail_form').id,
            'target': 'new',
            'context': self.env.context,
        }
    
    # ==================== ONCHANGE METHODS ====================
    
    @api.onchange('gutter_bracket_type')
    def _onchange_gutter_bracket_type(self):
        if self.gutter_bracket_type == 'none':
            pass
    
    @api.onchange('enable_zigzag_wire')
    def _onchange_enable_zigzag_wire(self):
        if not self.enable_zigzag_wire:
            self.zigzag_wire_size = '1.4'
    
    @api.onchange('column_bracket_type')
    def _onchange_column_bracket_type(self):
        if self.column_bracket_type == 'none':
            pass
    
    @api.onchange('enable_rollup_connectors')
    def _onchange_enable_rollup_connectors(self):
        if not self.enable_rollup_connectors:
            pass
            
    @api.onchange('clamp_type')
    def _onchange_clamp_type(self):
        if self.clamp_type == 'none':
            self.big_purlin_clamp_type_first = False
            self.big_purlin_clamp_type_second = False
            self.small_purlin_clamp_type_first = False
            self.small_purlin_clamp_type_second = False
            self.bottom_chord_clamp_type = 'single'
        elif self.clamp_type == 'w_type':
            self.bottom_chord_clamp_type = 'single'
            if not self.big_purlin_clamp_type_first:
                self.big_purlin_clamp_type_first = 'full_clamp'
            if not self.big_purlin_clamp_type_second:
                self.big_purlin_clamp_type_second = 'half_clamp'
            if not self.small_purlin_clamp_type_first:
                self.small_purlin_clamp_type_first = 'full_clamp'
            if not self.small_purlin_clamp_type_second:
                self.small_purlin_clamp_type_second = 'half_clamp'
        elif self.clamp_type == 'm_type':
            if not self.bottom_chord_clamp_type:
                self.bottom_chord_clamp_type = 'single'
            self.big_purlin_clamp_type_first = False
            self.big_purlin_clamp_type_second = False
            self.small_purlin_clamp_type_first = False
            self.small_purlin_clamp_type_second = False