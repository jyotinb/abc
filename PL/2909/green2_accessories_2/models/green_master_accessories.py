# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from math import ceil
import logging
_logger = logging.getLogger(__name__)

class GreenMaster(models.Model):
    _inherit = 'green.master'
    
    gutter_bracket_type = fields.Selection([('arch', 'Gutter Arch Bracket'),('f_bracket', 'F Bracket'),('none', 'None')], string='Gutter Bracket Type', default='none', tracking=True)
    enable_zigzag_wire = fields.Boolean('Enable Zigzag Wire', default=False, tracking=True)
    zigzag_wire_size = fields.Selection([('1.4', '1.4'),('1.5', '1.5'),('1.6', '1.6')], string='Zigzag Wire Size', default='1.4', tracking=True)
    column_bracket_type = fields.Selection([('l_bracket', 'L Bracket'),('clamps', 'Clamps'),('none', 'None')], string='Column Bracket Type', default='none', tracking=True)
    enable_rollup_connectors = fields.Boolean('Enable Roll Up Connectors', default=False, tracking=True)
    profiles_for_arch = fields.Float('Profiles For Arch', compute='_compute_all_profiles', store=True)
    profile_for_purlin = fields.Float('Profile For Purlin', compute='_compute_all_profiles', store=True)
    profile_for_bottom = fields.Float('Profile for Bottom', compute='_compute_all_profiles', store=True)
    side_profile = fields.Float('Side Profile', compute='_compute_all_profiles', store=True)
    door_profile = fields.Float('Door Profile', compute='_compute_all_profiles', store=True)
    total_profile = fields.Float('Total Profile', compute='_compute_all_profiles', store=True)
    enable_foundation_rods = fields.Boolean('Enable Foundation Rods', default=False, tracking=True)
    foundation_rods_per_foundation = fields.Integer('Rods per Foundation', default=2, tracking=True)
    foundation_rods_per_asc = fields.Integer('Rods per ASC Pipe', default=2, tracking=True)
    clamp_type = fields.Selection([('w_type', 'W Type'),('m_type', 'M Type'),('none', 'None')], string='Clamp Type', default='none', tracking=True)
    big_purlin_clamp_type_first = fields.Selection([('full_clamp', 'Full Clamp'),('l_joint', 'L Joint'),], string='Big Purlin First Type', tracking=True)
    big_purlin_clamp_type_second = fields.Selection([('half_clamp', 'Half Clamp'),('t_joint', 'T Joint'),], string='Big Purlin Second Type', tracking=True)
    small_purlin_clamp_type_first = fields.Selection([('full_clamp', 'Full Clamp'),('l_joint', 'L Joint'),], string='Small Purlin First Type', tracking=True)
    small_purlin_clamp_type_second = fields.Selection([('half_clamp', 'Half Clamp'),('t_joint', 'T Joint'),], string='Small Purlin Second Type', tracking=True)
    bottom_chord_clamp_type = fields.Selection([('single', 'Single'),('triple', 'Triple')], string='Bottom Chord Clamp Type', default='single', tracking=True)
    border_purlin_clamps_summary = fields.Text(string='Border Purlin Clamps Summary',compute='_compute_border_purlin_clamps_summary',store=False)
    bay_side_clamp_required = fields.Boolean(string='Bay Side Clamp Required',store=True)
    accessories_component_ids = fields.One2many('accessories.component.line','green_master_id',string='Accessories Components')
    brackets_component_ids = fields.One2many('accessories.component.line','green_master_id',domain=[('section', '=', 'brackets')],string='Brackets Components')
    wires_connectors_component_ids = fields.One2many('accessories.component.line','green_master_id',domain=[('section', '=', 'wires_connectors')],string='Wires & Connectors Components')
    clamps_component_ids = fields.One2many('accessories.component.line','green_master_id',domain=[('section', '=', 'clamps')],string='Clamps Components')
    profiles_component_ids = fields.One2many('accessories.component.line','green_master_id',domain=[('section', '=', 'profiles')],string='Profiles Components')
    foundation_component_ids = fields.One2many('accessories.component.line','green_master_id',domain=[('section', '=', 'foundation')],string='Foundation Components')
    clamps_size_summary = fields.Text(string='Clamps Size Summary',compute='_compute_clamps_size_summary',store=False)
    total_profiles_cost = fields.Float('Total Profiles Cost',compute='_compute_accessories_totals', store=True, tracking=True)
    total_foundation_cost = fields.Float('Total Foundation Cost',compute='_compute_accessories_totals', store=True, tracking=True)
    total_brackets_cost = fields.Float('Total Brackets Cost',compute='_compute_accessories_totals', store=True, tracking=True)
    total_wires_connectors_cost = fields.Float('Total Wires & Connectors Cost',compute='_compute_accessories_totals', store=True, tracking=True)
    total_clamps_cost = fields.Float('Total Clamps Cost',compute='_compute_accessories_totals', store=True, tracking=True)
    total_accessories_cost = fields.Float('Total Accessories Cost',compute='_compute_accessories_totals', store=True, tracking=True)
    
    @api.depends('brackets_component_ids.total_cost', 'wires_connectors_component_ids.total_cost','clamps_component_ids.total_cost', 'foundation_component_ids.total_cost','profiles_component_ids.total_cost')
    def _compute_accessories_totals(self):
        for record in self:
            record.total_brackets_cost = sum(record.brackets_component_ids.mapped('total_cost'))
            record.total_wires_connectors_cost = sum(record.wires_connectors_component_ids.mapped('total_cost'))
            record.total_clamps_cost = sum(record.clamps_component_ids.mapped('total_cost'))
            record.total_foundation_cost = sum(record.foundation_component_ids.mapped('total_cost'))
            record.total_profiles_cost = sum(record.profiles_component_ids.mapped('total_cost'))
            record.total_accessories_cost = (record.total_brackets_cost + record.total_wires_connectors_cost + record.total_clamps_cost + record.total_foundation_cost + record.total_profiles_cost)
    
    @api.depends('clamps_component_ids', 'bay_side_border_purlin', 'span_side_border_purlin')
    def _compute_border_purlin_clamps_summary(self):
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
        for record in self:
            has_bay_asc = record.width_front_bay_coridoor > 0 or record.width_back_bay_coridoor > 0
            has_bay_border = int(record.bay_side_border_purlin) > 0
            record.bay_side_clamp_required = has_bay_asc and has_bay_border
    
    @api.depends('no_of_spans', 'span_length', 'small_arch_length', 'big_arch_length','length_vent_big_arch_support', 'length_vent_small_arch_support','truss_component_ids.total_length', 'lower_component_ids.total_length','asc_component_ids.total_length', 'gutter_type', 'column_height','is_side_coridoors', 'bay_width', 'bay_length')
    def _compute_all_profiles(self):
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
        try:
            profile_for_bottom = self.span_length * 2
            return profile_for_bottom
        except Exception as e:
            _logger.error(f"Error calculating profile for bottom: {e}")
            return 0

    def _calculate_side_profile(self):
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
                asc_component_names = ['Front Span ASC Pipes', 'Back Span ASC Pipes','Front Bay ASC Pipes', 'Back Bay ASC Pipes']
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
        try:
            profiles_for_arch = self._calculate_profiles_for_arch()
            profile_for_purlin = self._calculate_profile_for_purlin()
            profile_for_bottom = self._calculate_profile_for_bottom()
            side_profile = self._calculate_side_profile()
            door_profile = self._calculate_door_profile()
            total_profile = (profiles_for_arch + profile_for_purlin + profile_for_bottom + side_profile + door_profile)
            return total_profile
        except Exception as e:
            _logger.error(f"Error calculating total profile: {e}")
            return 0
    
    def _create_total_profile_component(self):
        if self.total_profile > 0:
            master_record = self.env['accessories.master'].search([('name', '=', 'Total Profile'),('category', '=', 'profiles'),('active', '=', True)], limit=1)
            unit_price = master_record.unit_price if master_record else 5.00
            self._create_accessory_component('profiles', 'Total Profile',int(self.total_profile), 'meters', unit_price)
    
    @api.depends('clamps_component_ids', 'clamps_component_ids.size_specification', 'clamps_component_ids.nos')
    def _compute_clamps_size_summary(self):
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
    
    @api.depends('total_asc_cost', 'total_frame_cost', 'total_truss_cost','total_lower_cost', 'total_accessories_cost')
    def _compute_section_totals(self):
        super()._compute_section_totals()
        for record in self:
            record.grand_total_cost += record.total_accessories_cost
    
    @api.constrains('enable_rollup_connectors', 'no_of_curtains')
    def _check_rollup_connectors(self):
        for record in self:
            if record.enable_rollup_connectors and record.no_of_curtains <= 0:
                raise ValidationError(_('Number of curtains must be greater than 0 when Roll Up Connectors are enabled.'))
    
    def action_calculate_process(self):
        result = super().action_calculate_process()
        for record in self:
            try:
                record._calculate_all_accessories()
            except Exception as e:
                _logger.error(f"Error calculating accessories: {e}")
        return result
    
    def _calculate_all_accessories(self):
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
        if self.accessories_component_ids:
            self.accessories_component_ids.unlink()
    
    def _calculate_gutter_brackets(self):
        if self.gutter_bracket_type == 'arch':
            if self.last_span_gutter:
                qty = (self.no_of_spans + 1) * (self.no_of_bays + 1)
                self._create_accessory_component('brackets', 'Gutter Arch Bracket HDGI 5.0 MM', qty, '5.0 MM')
            else:
                qty_main = (self.no_of_spans - 1) * (self.no_of_bays + 1)
                self._create_accessory_component('brackets', 'Gutter Arch Bracket HDGI 5.0 MM', qty_main, '5.0 MM')
                qty_half = self.no_of_bays + 1
                self._create_accessory_component('brackets', 'Gutter Arch Bracket HDGI Half Left', qty_half, 'Half')
                self._create_accessory_component('brackets', 'Gutter Arch Bracket HDGI Half Right', qty_half, 'Half')
        elif self.gutter_bracket_type == 'f_bracket':
            big_arch_count = self._get_big_arch_count()
            self._create_accessory_component('brackets', 'F Bracket Big', big_arch_count, 'Big')
            small_arch_count = self._get_small_arch_count()
            self._create_accessory_component('brackets', 'F Bracket Small', small_arch_count, 'Small')
    
    def _calculate_zigzag_wire(self):
        if self.enable_zigzag_wire:
            total_profile = self.total_profile
            if total_profile <= 0:
                total_profile = self._calculate_total_profile()
            wire_length_needed = total_profile
            if wire_length_needed > 0:
                self._create_accessory_component('wires_connectors', f'Zigzag Wire {self.zigzag_wire_size}',int(wire_length_needed), self.zigzag_wire_size)
    
    def _calculate_column_brackets(self):
        middle_columns_count = self._get_middle_columns_count()
        if middle_columns_count <= 0:
            return
        if self.column_bracket_type == 'l_bracket':
            qty = middle_columns_count * 2
            self._create_accessory_component('brackets', 'L Bracket', qty, 'Standard')
        elif self.column_bracket_type == 'clamps':
            pipe_size = self._get_middle_column_pipe_size()
            clamp_component = self._create_accessory_component('clamps', 'Clamps', middle_columns_count, pipe_size)
            if clamp_component:
                clamp_component.auto_detected_size = pipe_size
    
    def _calculate_rollup_connectors(self):
        if self.enable_rollup_connectors and self.no_of_curtains > 0:
            self._create_accessory_component('wires_connectors', 'Roll Up Connector Smooth',self.no_of_curtains, 'Standard')
            self._create_accessory_component('wires_connectors', 'Roll Up Connector Handle',self.no_of_curtains, 'Standard')
    
    def _calculate_foundation_rods(self):
        if self.enable_foundation_rods:
            foundations_count = self._get_foundations_count()
            asc_pipes_count = self._get_asc_pipes_count()
            total_rods = (foundations_count * self.foundation_rods_per_foundation) + (asc_pipes_count * self.foundation_rods_per_asc)
            if total_rods > 0:
                self._create_accessory_component('foundation','Foundation Rods',total_rods,'Standard')
    
    def _calculate_advanced_clamps(self):
        if self.clamp_type == 'none' and not (self.is_side_coridoors and self.support_hockeys > 0):
            if (int(self.bay_side_border_purlin) <= 0 and int(self.span_side_border_purlin) <= 0 and 
                self.arch_middle_purlin_big_arch == '0' and self.arch_middle_purlin_small_arch == '0' and 
                not (self.is_bottom_chord and int(self.v_support_bottom_chord_frame) > 0) and
                self.gutter_bracket_type not in ['f_bracket', 'arch']):
                return
        
        clamp_accumulator = {}
        
        # W Type or M Type clamps
        if self.clamp_type == 'w_type':
            self._accumulate_w_type_clamps(clamp_accumulator)
        elif self.clamp_type == 'm_type':
            self._accumulate_m_type_clamps(clamp_accumulator)
        
        # V Support to Main Column clamps
        if self.is_bottom_chord and int(self.v_support_bottom_chord_frame) > 0:
            self._accumulate_v_support_main_column_clamps(clamp_accumulator)
        
        # ASC Support clamps (for Hockey/Support) - EXISTING
        if self.is_side_coridoors and self.support_hockeys > 0:
            self._accumulate_asc_support_clamps(clamp_accumulator)
        
        # ASC Bracket clamps (for F Bracket / Gutter Arch) - NEW
        if self.gutter_bracket_type in ['f_bracket', 'arch']:
            self._accumulate_asc_bracket_clamps(clamp_accumulator)
        
        # Border Purlin clamps
        self._accumulate_border_purlin_clamps(clamp_accumulator)
        
        # Arch Middle Purlin clamps
        self._accumulate_arch_middle_purlin_clamps(clamp_accumulator)
        
        # Create clamp components from accumulator
        self._create_clamp_components_from_accumulator(clamp_accumulator)
    
    def _accumulate_v_support_main_column_clamps(self, accumulator):
        if not self.is_bottom_chord or int(self.v_support_bottom_chord_frame) <= 0:
            return
        no_of_af_lines = self.no_anchor_frame_lines
        no_of_bays = self.no_of_bays
        no_of_spans = self.no_of_spans
        thick_config = self.thick_column
        main_column_size = self._get_main_column_pipe_size()
        af_main_column_size = self._get_af_main_column_pipe_size()
        thick_column_size = self._get_thick_column_pipe_size()
        if no_of_bays <= 0 or no_of_spans <= 0:
            return
        if thick_config == '0':
            if no_of_af_lines > 0 and af_main_column_size:
                af_full_qty = no_of_af_lines * 2
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_column_size, af_full_qty)
            if main_column_size:
                main_full_qty = (no_of_bays + 1 - no_of_af_lines) * 2
                if main_full_qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_column_size, main_full_qty)
        elif thick_config == '1':
            if thick_column_size:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_column_size, 4)
            corners_from_af = min(4, no_of_af_lines * 2)
            corners_from_main = 4 - corners_from_af
            if no_of_af_lines > 0 and af_main_column_size:
                af_full_qty = max(0, (no_of_af_lines * 2) - corners_from_af)
                if af_full_qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_column_size, af_full_qty)
            if main_column_size:
                main_full_qty = max(0, ((no_of_bays + 1 - no_of_af_lines) * 2) - corners_from_main)
                if main_full_qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_column_size, main_full_qty)
        elif thick_config == '2':
            if thick_column_size:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_column_size, (no_of_bays + 1) * 2)
        elif thick_config == '3':
            if no_of_af_lines > 0 and af_main_column_size:
                af_full_qty = no_of_af_lines * 2
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_column_size, af_full_qty)
            if main_column_size:
                main_full_qty = (no_of_bays + 1 - no_of_af_lines) * 2
                if main_full_qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_column_size, main_full_qty)
        elif thick_config == '4':
            if thick_column_size:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_column_size, (no_of_bays + 1) * 2)
        if no_of_spans > 1:
            if thick_config == '0':
                if no_of_af_lines > 0 and af_main_column_size:
                    af_half_qty = no_of_af_lines * (no_of_spans - 1)
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', af_main_column_size, af_half_qty)
                if main_column_size:
                    main_half_qty = (no_of_bays + 1 - no_of_af_lines) * (no_of_spans - 1)
                    if main_half_qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', main_column_size, main_half_qty)
            elif thick_config == '1':
                if no_of_af_lines > 0 and af_main_column_size:
                    af_half_qty = no_of_af_lines * (no_of_spans - 1)
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', af_main_column_size, af_half_qty)
                if main_column_size:
                    main_half_qty = (no_of_bays + 1 - no_of_af_lines) * (no_of_spans - 1)
                    if main_half_qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', main_column_size, main_half_qty)
            elif thick_config == '2':
                if thick_column_size:
                    total_half_qty = (no_of_bays + 1) * (no_of_spans - 1)
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', thick_column_size, total_half_qty)
            elif thick_config == '3':
                if no_of_af_lines > 0 and af_main_column_size:
                    af_half_qty = no_of_af_lines * (no_of_spans - 1)
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', af_main_column_size, af_half_qty)
                if main_column_size:
                    main_half_qty = (no_of_bays + 1 - no_of_af_lines) * (no_of_spans - 1)
                    if main_half_qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', main_column_size, main_half_qty)
            elif thick_config == '4':
                if thick_column_size:
                    total_half_qty = (no_of_bays + 1) * (no_of_spans - 1)
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', thick_column_size, total_half_qty)

    def _accumulate_w_type_clamps(self, accumulator):
        bottom_chord_data = self._get_bottom_chord_data()
        bottom_chord_data['count'] = ceil(bottom_chord_data['count'] - (bottom_chord_data.get('afs_count', 0)/2))
        v_support_count = self._get_v_support_count()
        big_arch_data = self._get_big_arch_data()
        small_arch_data = self._get_small_arch_data()
        vent_support_big_arch = self._get_vent_support_big_arch_count()
        arch_support_straight_middle_data = self._get_arch_support_straight_middle_data()
        middle_column_data = self._get_middle_column_data()
        if bottom_chord_data['count'] > 0 and bottom_chord_data['size']:
            qty = (bottom_chord_data['count'] * 3) + v_support_count
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', bottom_chord_data['size'], qty)
        if big_arch_data['count'] > 0 and big_arch_data['size']:
            qty = (big_arch_data['count'] * 2) + vent_support_big_arch
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], qty)
        if small_arch_data['count'] > 0 and small_arch_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_data['size'], small_arch_data['count'])
        if arch_support_straight_middle_data['count'] > 0 and arch_support_straight_middle_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp',arch_support_straight_middle_data['size'],arch_support_straight_middle_data['count'])
            self._add_to_clamp_accumulator(accumulator, 'Half Clamp',arch_support_straight_middle_data['size'],arch_support_straight_middle_data['count'])
        if middle_column_data['count'] > 0 and middle_column_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp',middle_column_data['size'],middle_column_data['count'])
            self._add_to_clamp_accumulator(accumulator, 'Half Clamp',middle_column_data['size'],middle_column_data['count'])
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
        bottom_chord_data = self._get_bottom_chord_data()
        bottom_chord_data['count'] = ceil(bottom_chord_data['count'] - (bottom_chord_data.get('afs_count', 0)/2))
        v_support_count = self._get_v_support_count()
        big_arch_data = self._get_big_arch_data()
        small_arch_data = self._get_small_arch_data()
        vent_support_big_arch = self._get_vent_support_big_arch_count()
        arch_support_straight_middle_data = self._get_arch_support_straight_middle_data()
        middle_column_data = self._get_middle_column_data()
        if bottom_chord_data['count'] > 0 and bottom_chord_data['size']:
            if self.bottom_chord_clamp_type == 'single':
                qty = (bottom_chord_data['count'] * 3) + v_support_count
            else:
                qty = (bottom_chord_data['count'] * 5) + v_support_count
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', bottom_chord_data['size'], qty)
        if big_arch_data['count'] > 0 and big_arch_data['size']:
            qty = (big_arch_data['count'] * 2) + vent_support_big_arch
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], qty)
        if small_arch_data['count'] > 0 and small_arch_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_data['size'], small_arch_data['count'])
        if arch_support_straight_middle_data['count'] > 0 and arch_support_straight_middle_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp',arch_support_straight_middle_data['size'],arch_support_straight_middle_data['count'])
        if middle_column_data['count'] > 0 and middle_column_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp',middle_column_data['size'],middle_column_data['count'])

    def _accumulate_asc_support_clamps(self, accumulator):
        asc_support_count = self._get_asc_support_pipes_count()
        asc_pipe_size = self._get_asc_pipe_size()
        if asc_support_count > 0 and asc_pipe_size:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', asc_pipe_size, asc_support_count)
        column_clamps = self._calculate_asc_column_clamps()
        if column_clamps['thick_count'] > 0:
            thick_size = self._get_thick_column_pipe_size()
            if thick_size:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, column_clamps['thick_count'])
        if column_clamps['middle_count'] > 0:
            middle_size = self._get_middle_column_pipe_size()
            if middle_size:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, column_clamps['middle_count'])
        if column_clamps.get('af_main_count', 0) > 0:
            af_main_size = self._get_af_main_column_pipe_size()
            if af_main_size and af_main_size != self._get_main_column_pipe_size():
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_size, column_clamps['af_main_count'])
        if column_clamps['main_count'] > 0:
            main_size = self._get_main_column_pipe_size()
            if main_size:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, column_clamps['main_count'])
    
    def _accumulate_asc_bracket_clamps(self, accumulator):
        """Accumulate ASC bracket clamps (F Bracket or Gutter Arch Bracket)"""
        
        # Get pipe sizes
        thick_column_size = self._get_thick_column_pipe_size()
        main_column_size = self._get_main_column_pipe_size()
        af_main_column_size = self._get_af_main_column_pipe_size()
        big_column_size = self._get_big_column_pipe_size()
        
        # Get configuration values
        thick_config = self.thick_column  # '0', '1', '2', '3', '4'
        no_of_spans = self.no_of_spans
        no_of_bays = self.no_of_bays
        no_af_lines = self.no_anchor_frame_lines
        no_big_column_per_af = int(self.no_column_big_frame) if self.no_column_big_frame else 0
        
        # Check ASC existence
        has_front_span_asc = self.width_front_span_coridoor > 0
        has_back_span_asc = self.width_back_span_coridoor > 0
        has_front_bay_asc = self.width_front_bay_coridoor > 0
        has_back_bay_asc = self.width_back_bay_coridoor > 0
        
        # SPAN ASC CLAMPS (for both F Bracket and Gutter Arch Bracket)
        
        # Front Span ASC
        if has_front_span_asc:
            if thick_config in ['1', '2']:  # 4 Corner OR 2 Bay Side
                # Thick Column clamps
                if thick_column_size:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_column_size, 2)
                
                # AF Main Column or Main Column clamps
                if no_af_lines >= 1:
                    # Big Column clamps
                    if big_column_size and no_big_column_per_af > 0:
                        qty = no_of_spans * no_big_column_per_af
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_column_size, qty)
                    # AF Main Column clamps
                    if af_main_column_size:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_column_size, no_of_spans - 1)
                else:
                    # Main Column clamps
                    if main_column_size:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_column_size, no_of_spans - 1)
                        
            elif thick_config in ['3', '4']:  # 2 Span Side OR 4 Side
                # Thick Column clamps
                if thick_column_size:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_column_size, no_of_spans + 1)
                
                # Big Column clamps (no AF Main/Main column for this config)
                if no_af_lines >= 1 and big_column_size and no_big_column_per_af > 0:
                    qty = no_of_spans * no_big_column_per_af
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_column_size, qty)
                    
            else:  # thick_config == '0' (No thick columns)
                if no_af_lines >= 1:
                    # Big Column clamps
                    if big_column_size and no_big_column_per_af > 0:
                        qty = no_of_spans * no_big_column_per_af
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_column_size, qty)
                    # AF Main Column clamps
                    if af_main_column_size:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_column_size, no_of_spans + 1)
                else:
                    # Main Column clamps
                    if main_column_size:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_column_size, no_of_spans + 1)
        
        # Back Span ASC
        if has_back_span_asc:
            if thick_config in ['1', '2']:  # 4 Corner OR 2 Bay Side
                # Thick Column clamps
                if thick_column_size:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_column_size, 2)
                
                # AF Main Column or Main Column clamps
                if no_af_lines >= 2:  # Note: >= 2 for Back Span
                    # Big Column clamps
                    if big_column_size and no_big_column_per_af > 0:
                        qty = no_of_spans * no_big_column_per_af
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_column_size, qty)
                    # AF Main Column clamps
                    if af_main_column_size:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_column_size, no_of_spans - 1)
                else:
                    # Main Column clamps
                    if main_column_size:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_column_size, no_of_spans - 1)
                        
            elif thick_config in ['3', '4']:  # 2 Span Side OR 4 Side
                # Thick Column clamps
                if thick_column_size:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_column_size, no_of_spans + 1)
                
                # Big Column clamps (no AF Main/Main column for this config)
                if no_af_lines >= 2 and big_column_size and no_big_column_per_af > 0:  # Note: >= 2 for Back Span
                    qty = no_of_spans * no_big_column_per_af
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_column_size, qty)
                    
            else:  # thick_config == '0' (No thick columns)
                if no_af_lines >= 2:  # Note: >= 2 for Back Span
                    # Big Column clamps
                    if big_column_size and no_big_column_per_af > 0:
                        qty = no_of_spans * no_big_column_per_af
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_column_size, qty)
                    # AF Main Column clamps
                    if af_main_column_size:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_column_size, no_of_spans + 1)
                else:
                    # Main Column clamps
                    if main_column_size:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_column_size, no_of_spans + 1)
        
        # BAY ASC CLAMPS (only for Gutter Arch Bracket with Bay Side Clamp Required = Yes)
        if self.gutter_bracket_type == 'arch' and self.bay_side_clamp_required:
            
            # Front Bay ASC
            if has_front_bay_asc:
                if thick_config in ['1', '3']:  # 4 Corner OR 2 Span Side
                    # Thick Column clamps
                    if thick_column_size:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_column_size, 2)
                    # Main Column clamps
                    if main_column_size:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_column_size, no_of_bays - 1)
                        
                elif thick_config in ['2', '4']:  # 2 Bay Side OR 4 Side
                    # Thick Column clamps
                    if thick_column_size:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_column_size, no_of_bays + 1)
                        
                else:  # thick_config == '0' (No thick columns)
                    # Main Column clamps
                    if main_column_size:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_column_size, no_of_bays + 1)
            
            # Back Bay ASC
            if has_back_bay_asc:
                if thick_config in ['1', '3']:  # 4 Corner OR 2 Span Side
                    # Thick Column clamps
                    if thick_column_size:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_column_size, 2)
                    # Main Column clamps
                    if main_column_size:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_column_size, no_of_bays - 1)
                        
                elif thick_config in ['2', '4']:  # 2 Bay Side OR 4 Side
                    # Thick Column clamps
                    if thick_column_size:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_column_size, no_of_bays + 1)
                        
                else:  # thick_config == '0' (No thick columns)
                    # Main Column clamps
                    if main_column_size:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_column_size, no_of_bays + 1)

    def _calculate_asc_column_clamps(self):
        thick_columns_to_consider = 0
        middle_columns_to_consider = 0
        af_main_columns_to_consider = 0
        has_front_span = self.width_front_span_coridoor > 0
        has_back_span = self.width_back_span_coridoor > 0
        has_front_bay = self.width_front_bay_coridoor > 0
        has_back_bay = self.width_back_bay_coridoor > 0
        big_columns_per_af = int(self.no_column_big_frame)
        no_of_af_lines = self.no_anchor_frame_lines
        af_main_size = self._get_af_main_column_pipe_size()
        main_size = self._get_main_column_pipe_size()
        af_main_different = (af_main_size != main_size) and af_main_size is not None
        if self.thick_column == '0':
            if has_front_span:
                middle_columns_to_consider += self.no_of_spans * big_columns_per_af
                if af_main_different and no_of_af_lines > 0:
                    af_main_columns_to_consider += no_of_af_lines
            if has_back_span:
                middle_columns_to_consider += self.no_of_spans * big_columns_per_af
                if af_main_different and no_of_af_lines > 0:
                    af_main_columns_to_consider += no_of_af_lines
        elif self.thick_column == '1':
            if has_front_span:
                thick_columns_to_consider += 2
                middle_columns_to_consider += self.no_of_spans * big_columns_per_af
                if af_main_different and no_of_af_lines > 0:
                    af_main_columns_to_consider += max(0, no_of_af_lines - 1)
            if has_back_span:
                thick_columns_to_consider += 2
                middle_columns_to_consider += self.no_of_spans * big_columns_per_af
                if af_main_different and no_of_af_lines > 0:
                    af_main_columns_to_consider += max(0, no_of_af_lines - 1)
            if has_front_bay:
                thick_columns_to_consider += 2
            if has_back_bay:
                thick_columns_to_consider += 2
        elif self.thick_column == '2':
            if has_front_span:
                thick_columns_to_consider += 2
                middle_columns_to_consider += self.no_of_spans * big_columns_per_af
                if af_main_different and no_of_af_lines > 0:
                    af_main_columns_to_consider += no_of_af_lines
            if has_back_span:
                thick_columns_to_consider += 2
                middle_columns_to_consider += self.no_of_spans * big_columns_per_af
                if af_main_different and no_of_af_lines > 0:
                    af_main_columns_to_consider += no_of_af_lines
            if has_front_bay:
                thick_columns_to_consider += self.no_of_bays + 1
            if has_back_bay:
                thick_columns_to_consider += self.no_of_bays + 1
        elif self.thick_column == '3':
            if has_front_span:
                thick_columns_to_consider += self.no_of_spans + 1
                middle_columns_to_consider += self.no_of_spans * big_columns_per_af
            if has_back_span:
                thick_columns_to_consider += self.no_of_spans + 1
                middle_columns_to_consider += self.no_of_spans * big_columns_per_af
            if has_front_bay:
                thick_columns_to_consider += 2
                if af_main_different and no_of_af_lines > 0:
                    af_main_columns_to_consider += max(0, no_of_af_lines - 1)
            if has_back_bay:
                thick_columns_to_consider += 2
                if af_main_different and no_of_af_lines > 0:
                    af_main_columns_to_consider += max(0, no_of_af_lines - 1)
        elif self.thick_column == '4':
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
            af_main_columns_to_consider = 0
        thick_clamp_count = thick_columns_to_consider * self.support_hockeys
        middle_clamp_count = middle_columns_to_consider * self.support_hockeys
        af_main_clamp_count = af_main_columns_to_consider * self.support_hockeys
        total_asc_support = self._get_asc_support_pipes_count()
        main_clamp_count = total_asc_support - (thick_clamp_count + middle_clamp_count + af_main_clamp_count)
        main_clamp_count = max(0, main_clamp_count)
        return {'thick_count': thick_clamp_count,'middle_count': middle_clamp_count,'af_main_count': af_main_clamp_count,'main_count': main_clamp_count}
    
    def _accumulate_border_purlin_clamps(self, accumulator):
        try:
            if int(self.bay_side_border_purlin) > 0:
                self._accumulate_bay_side_border_clamps(accumulator)
            if int(self.span_side_border_purlin) > 0:
                self._accumulate_span_side_border_clamps(accumulator)
                if self.no_anchor_frame_lines >= 1:
                    self._accumulate_anchor_frame_clamps(accumulator)
        except Exception as e:
            _logger.error(f"Error accumulating border purlin clamps: {e}")
    
    def _accumulate_bay_side_border_clamps(self, accumulator):
        try:
            bay_side_value = int(self.bay_side_border_purlin)
            if bay_side_value <= 0:
                return
            if self.width_front_bay_coridoor > 0:
                pipe_size = self._get_asc_pipe_size()
                if pipe_size:
                    half_qty = (self.no_of_bays - 1) * bay_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', pipe_size, half_qty)
                    full_qty = 2 * bay_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', pipe_size, full_qty)
            else:
                half_size, full_size = self._get_bay_side_pipe_sizes('front')
                if half_size and full_size:
                    half_qty = (self.no_of_bays - 1) * bay_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', half_size, half_qty)
                    full_qty = 2 * bay_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', full_size, full_qty)
            if self.width_back_bay_coridoor > 0:
                pipe_size = self._get_asc_pipe_size()
                if pipe_size:
                    half_qty = (self.no_of_bays - 1) * bay_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', pipe_size, half_qty)
                    full_qty = 2 * bay_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', pipe_size, full_qty)
            else:
                half_size, full_size = self._get_bay_side_pipe_sizes('back')
                if half_size and full_size:
                    half_qty = (self.no_of_bays - 1) * bay_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', half_size, half_qty)
                    full_qty = 2 * bay_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', full_size, full_qty)
        except Exception as e:
            _logger.error(f"Error calculating bay side border clamps: {e}")
    
    def _accumulate_span_side_border_clamps(self, accumulator):
        try:
            span_side_value = int(self.span_side_border_purlin)
            if span_side_value <= 0:
                return
            if self.width_front_span_coridoor > 0:
                pipe_size = self._get_asc_pipe_size()
                if pipe_size:
                    half_qty = (self.no_of_spans - 1) * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', pipe_size, half_qty)
                    full_qty = 2 * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', pipe_size, full_qty)
            else:
                half_size, full_size = self._get_span_side_pipe_sizes('front')
                if half_size and full_size:
                    half_qty = (self.no_of_spans - 1) * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', half_size, half_qty)
                    full_qty = 2 * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', full_size, full_qty)
            if self.width_back_span_coridoor > 0:
                pipe_size = self._get_asc_pipe_size()
                if pipe_size:
                    half_qty = (self.no_of_spans - 1) * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', pipe_size, half_qty)
                    full_qty = 2 * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', pipe_size, full_qty)
            else:
                half_size, full_size = self._get_span_side_pipe_sizes('back')
                if half_size and full_size:
                    half_qty = (self.no_of_spans - 1) * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', half_size, half_qty)
                    full_qty = 2 * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', full_size, full_qty)
        except Exception as e:
            _logger.error(f"Error calculating span side border clamps: {e}")
    
    def _accumulate_anchor_frame_clamps(self, accumulator):
        try:
            span_side_value = int(self.span_side_border_purlin)
            if span_side_value <= 0 or self.no_anchor_frame_lines <= 0:
                return
            if self.no_anchor_frame_lines == 1:
                _logger.info("Anchor Frame Lines = 1: ASC and Anchor Frame Lines considered at same line")
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
                if self.width_front_span_coridoor > 0:
                    pipe_size = self._get_asc_pipe_size()
                else:
                    pipe_size = self._get_big_column_pipe_size()
                if pipe_size:
                    half_qty = self.no_of_spans * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', pipe_size, half_qty)
                if self.width_back_span_coridoor > 0:
                    pipe_size = self._get_asc_pipe_size()
                else:
                    pipe_size = self._get_big_column_pipe_size()
                if pipe_size:
                    half_qty = self.no_of_spans * span_side_value
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', pipe_size, half_qty)
        except Exception as e:
            _logger.error(f"Error calculating anchor frame clamps: {e}")
    
    def _accumulate_arch_middle_purlin_clamps(self, accumulator):
        if self.arch_middle_purlin_big_arch != '0' and int(self.arch_middle_purlin_big_arch_pcs) > 0:
            self._accumulate_big_arch_middle_purlin(accumulator)
        if self.arch_middle_purlin_small_arch != '0' and int(self.arch_middle_purlin_small_arch_pcs) > 0:
            self._accumulate_small_arch_middle_purlin(accumulator)

    def _accumulate_big_arch_middle_purlin(self, accumulator):
        config_value = self.arch_middle_purlin_big_arch
        pcs_value = int(self.arch_middle_purlin_big_arch_pcs)
        no_arch_middle_purlin_big_arch = 0
        arch_middle_purlin = self.lower_component_ids.filtered(lambda c: c.name == 'Arch Middle Purlin Big Arch')
        if arch_middle_purlin:
            no_arch_middle_purlin_big_arch = arch_middle_purlin.nos
        big_arch_data = self._get_big_arch_data()
        big_arch_size = big_arch_data['size']
        if not big_arch_size or no_arch_middle_purlin_big_arch == 0:
            return
        full_qty = 0
        if config_value == '1':
            full_qty = no_arch_middle_purlin_big_arch * 2
        elif config_value == '2':
            full_qty = no_arch_middle_purlin_big_arch * 2
        elif config_value == '3':
            full_qty = 4 * pcs_value
        elif config_value == '4':
            full_qty = ((((self.no_of_spans - 2) * 4) + 4) * pcs_value)
        elif config_value == '5':
            full_qty = self.no_of_spans * 2
        if full_qty > 0:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_size, full_qty)
        half_qty = 0
        if config_value == '3':
            half_qty = (no_arch_middle_purlin_big_arch * 2) - (4 * pcs_value)
        elif config_value == '4':
            half_qty = no_arch_middle_purlin_big_arch - (((((self.no_of_spans - 2) * 4) + 4) * pcs_value) / 2)
        elif config_value == '5':
            half_qty = self.no_of_spans * (self.no_of_bays - 1)
        if half_qty > 0:
            self._add_to_clamp_accumulator(accumulator, 'Half Clamp', big_arch_size, half_qty)

    def _accumulate_small_arch_middle_purlin(self, accumulator):
        config_value = self.arch_middle_purlin_small_arch
        pcs_value = int(self.arch_middle_purlin_small_arch_pcs)
        no_arch_middle_purlin_small_arch = 0
        arch_middle_purlin = self.lower_component_ids.filtered(lambda c: c.name == 'Arch Middle Purlin Small Arch')
        if arch_middle_purlin:
            no_arch_middle_purlin_small_arch = arch_middle_purlin.nos
        small_arch_data = self._get_small_arch_data()
        small_arch_size = small_arch_data['size']
        if not small_arch_size or no_arch_middle_purlin_small_arch == 0:
            return
        full_qty = 0
        if config_value == '1':
            full_qty = no_arch_middle_purlin_small_arch * 2
        elif config_value == '2':
            full_qty = no_arch_middle_purlin_small_arch * 2
        elif config_value == '3':
            full_qty = 4 * pcs_value
        elif config_value == '4':
            full_qty = ((((self.no_of_spans - 2) * 4) + 4) * pcs_value)
        elif config_value == '5':
            full_qty = self.no_of_spans * 2
        if full_qty > 0:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_size, full_qty)
        half_qty = 0
        if config_value == '3':
            half_qty = (no_arch_middle_purlin_small_arch * 2) - (4 * pcs_value)
        elif config_value == '4':
            half_qty = no_arch_middle_purlin_small_arch - (((((self.no_of_spans - 2) * 4) + 4) * pcs_value) / 2)
        elif config_value == '5':
            half_qty = self.no_of_spans * (self.no_of_bays - 1)
        if half_qty > 0:
            self._add_to_clamp_accumulator(accumulator, 'Half Clamp', small_arch_size, half_qty)
    
    def get_clamp_calculation_details(self):
        details = []
        sequence = 10
        
        # M Type or W Type clamps
        if self.clamp_type == 'm_type':
            details.extend(self._get_m_type_clamp_details(sequence))
            sequence += 100
        elif self.clamp_type == 'w_type':
            details.extend(self._get_w_type_clamp_details(sequence))
            sequence += 100
        
        # V Support to Main Column
        if self.is_bottom_chord and int(self.v_support_bottom_chord_frame) > 0:
            details.extend(self._get_v_support_main_column_details(sequence))
            sequence += 100
        
        # Cross Bracing
        details.extend(self._get_cross_bracing_details(sequence))
        sequence += 100
        
        # ASC Support (Hockey/Support) - EXISTING
        if self.is_side_coridoors and self.support_hockeys > 0:
            details.extend(self._get_asc_support_details(sequence))
            sequence += 100
        
        # ASC Brackets (F/Gutter Arch) - NEW
        if self.gutter_bracket_type in ['f_bracket', 'arch']:
            details.extend(self._get_asc_bracket_details(sequence))
            sequence += 100
        
        # Border Purlin
        if int(self.bay_side_border_purlin) > 0 or int(self.span_side_border_purlin) > 0:
            details.extend(self._get_border_purlin_details(sequence))
            sequence += 100
        
        # Arch Middle Purlin
        details.extend(self._get_arch_middle_purlin_details(sequence))
        
        return details

    def _get_m_type_clamp_details(self, sequence):
        details = []
        bottom_chord_data = self._get_bottom_chord_data()
        bottom_chord_data['count'] = ceil(bottom_chord_data['count'] - (bottom_chord_data.get('afs_count', 0)/2))
        v_support = self._get_v_support_count()
        if bottom_chord_data['count'] > 0 and bottom_chord_data['size']:
            multiplier = 3 if self.bottom_chord_clamp_type == 'single' else 5
            qty = (bottom_chord_data['count'] * multiplier) + v_support
            details.append({'sequence': sequence,'category': 'M TYPE CLAMPS','component': f"Bottom Chord ({self.bottom_chord_clamp_type.title()})",'clamp_type': 'Full Clamp','size': bottom_chord_data['size'],'quantity': int(qty),'formula': f"({bottom_chord_data['count']} × {multiplier}) + {v_support}",'unit_price': self._get_clamp_price('Full Clamp', bottom_chord_data['size']),})
            sequence += 10
        details.extend(self._get_common_arch_details('M TYPE CLAMPS', sequence))
        return details

    def _get_w_type_clamp_details(self, sequence):
        details = []
        
        bottom_chord_data = self._get_bottom_chord_data()
        bottom_chord_data['count'] = ceil(bottom_chord_data['count'] - (bottom_chord_data.get('afs_count', 0)/2))
        v_support = self._get_v_support_count()
        if bottom_chord_data['count'] > 0 and bottom_chord_data['size']:
            qty = (bottom_chord_data['count'] * 3) + v_support
            details.append({'sequence': sequence,'category': 'W TYPE CLAMPS','component': 'Bottom Chord','clamp_type': 'Full Clamp','size': bottom_chord_data['size'],'quantity': int(qty),'formula': f"({bottom_chord_data['count']} × 3) + {v_support}",'unit_price': self._get_clamp_price('Full Clamp', bottom_chord_data['size']),})
            sequence += 10
        details.extend(self._get_w_type_purlin_details(sequence))
        sequence += 50
        details.extend(self._get_common_arch_details('W TYPE CLAMPS', sequence))
        return details

    def _get_w_type_purlin_details(self, start_sequence):
        details = []
        sequence = start_sequence
        big_arch_data = self._get_big_arch_data()
        small_arch_data = self._get_small_arch_data()
        if big_arch_data['size'] and self.big_purlin_clamp_type_first:
            qty_first = self.no_of_spans * 2
            clamp_name = 'Full Clamp' if self.big_purlin_clamp_type_first == 'full_clamp' else 'L Joint'
            details.append({'sequence': sequence,'category': 'W TYPE CLAMPS','component': 'Big Purlin (First Type)','clamp_type': clamp_name,'size': big_arch_data['size'],'quantity': int(qty_first),'formula': f"No of Spans × 2 = {self.no_of_spans} × 2",'unit_price': self._get_clamp_price(clamp_name, big_arch_data['size']),})
            sequence += 10
            if self.big_purlin_clamp_type_second:
                qty_second = big_arch_data['count'] - qty_first
                if qty_second > 0:
                    clamp_name = 'Half Clamp' if self.big_purlin_clamp_type_second == 'half_clamp' else 'T Joint'
                    details.append({'sequence': sequence,'category': 'W TYPE CLAMPS','component': 'Big Purlin (Second Type)','clamp_type': clamp_name,'size': big_arch_data['size'],'quantity': int(qty_second),'formula': f"Remaining = {big_arch_data['count']} - {qty_first}",'unit_price': self._get_clamp_price(clamp_name, big_arch_data['size']),})
                    sequence += 10
        if small_arch_data['size'] and self.small_purlin_clamp_type_first:
            qty_first = self.no_of_spans * 2
            clamp_name = 'Full Clamp' if self.small_purlin_clamp_type_first == 'full_clamp' else 'L Joint'
            details.append({'sequence': sequence,'category': 'W TYPE CLAMPS','component': 'Small Purlin (First Type)','clamp_type': clamp_name,'size': small_arch_data['size'],'quantity': int(qty_first),'formula': f"No of Spans × 2 = {self.no_of_spans} × 2",'unit_price': self._get_clamp_price(clamp_name, small_arch_data['size']),})
            sequence += 10
            if self.small_purlin_clamp_type_second:
                qty_second = small_arch_data['count'] - qty_first
                if qty_second > 0:
                    clamp_name = 'Half Clamp' if self.small_purlin_clamp_type_second == 'half_clamp' else 'T Joint'
                    details.append({'sequence': sequence,'category': 'W TYPE CLAMPS','component': 'Small Purlin (Second Type)','clamp_type': clamp_name,'size': small_arch_data['size'],'quantity': int(qty_second),'formula': f"Remaining = {small_arch_data['count']} - {qty_first}",'unit_price': self._get_clamp_price(clamp_name, small_arch_data['size']),})
        return details

    def _get_common_arch_details(self, category, start_sequence):
        details = []
        sequence = start_sequence
        big_arch_data = self._get_big_arch_data()
        small_arch_data = self._get_small_arch_data()
        vent_support = self._get_vent_support_big_arch_count()
        if big_arch_data['count'] > 0 and big_arch_data['size']:
            qty = (big_arch_data['count'] * 2) + vent_support
            details.append({'sequence': sequence,'category': category,'component': 'Big Arch','clamp_type': 'Full Clamp','size': big_arch_data['size'],'quantity': int(qty),'formula': f"({big_arch_data['count']} × 2) + {vent_support}" if vent_support > 0 else f"{big_arch_data['count']} × 2",'unit_price': self._get_clamp_price('Full Clamp', big_arch_data['size']),})
            sequence += 10
        if small_arch_data['count'] > 0 and small_arch_data['size']:
            details.append({'sequence': sequence,'category': category,'component': 'Small Arch','clamp_type': 'Full Clamp','size': small_arch_data['size'],'quantity': int(small_arch_data['count']),'formula': f"Total Small Arches = {small_arch_data['count']}",'unit_price': self._get_clamp_price('Full Clamp', small_arch_data['size']),})
            sequence += 10
        if category == 'W TYPE CLAMPS':
            arch_support_data = self._get_arch_support_straight_middle_data()
            if arch_support_data['count'] > 0 and arch_support_data['size']:
                details.append({'sequence': sequence,'category': category,'component': 'Arch Support Straight','clamp_type': 'Full Clamp','size': arch_support_data['size'],'quantity': int(arch_support_data['count']),'formula': f"Total = {arch_support_data['count']}",'unit_price': self._get_clamp_price('Full Clamp', arch_support_data['size']),})
                sequence += 10
                details.append({'sequence': sequence,'category': category,'component': 'Arch Support Straight','clamp_type': 'Half Clamp','size': arch_support_data['size'],'quantity': int(arch_support_data['count']),'formula': f"Total = {arch_support_data['count']}",'unit_price': self._get_clamp_price('Half Clamp', arch_support_data['size']),})
        return details

    def _get_v_support_main_column_details(self, sequence):
        details = []
        if not self.is_bottom_chord or int(self.v_support_bottom_chord_frame) <= 0:
            return details
        no_of_af_lines = self.no_anchor_frame_lines
        no_of_bays = self.no_of_bays
        no_of_spans = self.no_of_spans
        thick_config = self.thick_column
        main_column_size = self._get_main_column_pipe_size()
        af_main_column_size = self._get_af_main_column_pipe_size()
        thick_column_size = self._get_thick_column_pipe_size()
        if thick_config == '0':
            if no_of_af_lines > 0 and af_main_column_size:
                af_full_qty = no_of_af_lines * 2
                details.append({'sequence': sequence,'category': 'V SUPPORT TO MAIN COLUMN - FULL CLAMPS','component': 'AF Main Column (End Connections)','clamp_type': 'Full Clamp','size': af_main_column_size,'quantity': int(af_full_qty),'formula': f"{no_of_af_lines} AF Lines × 2",'unit_price': self._get_clamp_price('Full Clamp', af_main_column_size),})
                sequence += 10
            if main_column_size:
                main_full_qty = (no_of_bays + 1 - no_of_af_lines) * 2
                if main_full_qty > 0:
                    details.append({'sequence': sequence,'category': 'V SUPPORT TO MAIN COLUMN - FULL CLAMPS','component': 'Main Column (End Connections)','clamp_type': 'Full Clamp','size': main_column_size,'quantity': int(main_full_qty),'formula': f"({no_of_bays + 1} - {no_of_af_lines}) × 2",'unit_price': self._get_clamp_price('Full Clamp', main_column_size),})
                    sequence += 10
        elif thick_config == '1':
            if thick_column_size:
                details.append({'sequence': sequence,'category': 'V SUPPORT TO MAIN COLUMN - FULL CLAMPS','component': 'Thick Column (4 Corners)','clamp_type': 'Full Clamp','size': thick_column_size,'quantity': 4,'formula': "4 Corner Positions",'unit_price': self._get_clamp_price('Full Clamp', thick_column_size),})
                sequence += 10
            corners_from_af = min(4, no_of_af_lines * 2)
            corners_from_main = 4 - corners_from_af
            if no_of_af_lines > 0 and af_main_column_size:
                af_full_qty = max(0, (no_of_af_lines * 2) - corners_from_af)
                if af_full_qty > 0:
                    details.append({'sequence': sequence,'category': 'V SUPPORT TO MAIN COLUMN - FULL CLAMPS','component': 'AF Main Column (After Corners)','clamp_type': 'Full Clamp','size': af_main_column_size,'quantity': int(af_full_qty),'formula': f"({no_of_af_lines} × 2) - {corners_from_af} corners",'unit_price': self._get_clamp_price('Full Clamp', af_main_column_size),})
                    sequence += 10
            if main_column_size:
                main_full_qty = max(0, ((no_of_bays + 1 - no_of_af_lines) * 2) - corners_from_main)
                if main_full_qty > 0:
                    details.append({'sequence': sequence,'category': 'V SUPPORT TO MAIN COLUMN - FULL CLAMPS','component': 'Main Column (After Corners)','clamp_type': 'Full Clamp','size': main_column_size,'quantity': int(main_full_qty),'formula': f"(({no_of_bays + 1} - {no_of_af_lines}) × 2) - {corners_from_main} corners",'unit_price': self._get_clamp_price('Full Clamp', main_column_size),})
                    sequence += 10
        elif thick_config == '2':
            if thick_column_size:
                details.append({'sequence': sequence,'category': 'V SUPPORT TO MAIN COLUMN - FULL CLAMPS','component': 'Thick Column (All Bay Side)','clamp_type': 'Full Clamp','size': thick_column_size,'quantity': int((no_of_bays + 1) * 2),'formula': f"({no_of_bays + 1}) × 2 (All Bay Side)",'unit_price': self._get_clamp_price('Full Clamp', thick_column_size),})
                sequence += 10
        elif thick_config == '3':
            if no_of_af_lines > 0 and af_main_column_size:
                af_full_qty = no_of_af_lines * 2
                details.append({'sequence': sequence,'category': 'V SUPPORT TO MAIN COLUMN - FULL CLAMPS','component': 'AF Main Column (Bay Side)','clamp_type': 'Full Clamp','size': af_main_column_size,'quantity': int(af_full_qty),'formula': f"{no_of_af_lines} AF Lines × 2",'unit_price': self._get_clamp_price('Full Clamp', af_main_column_size),})
                sequence += 10
            if main_column_size:
                main_full_qty = (no_of_bays + 1 - no_of_af_lines) * 2
                if main_full_qty > 0:
                    details.append({'sequence': sequence,'category': 'V SUPPORT TO MAIN COLUMN - FULL CLAMPS','component': 'Main Column (Bay Side)','clamp_type': 'Full Clamp','size': main_column_size,'quantity': int(main_full_qty),'formula': f"({no_of_bays + 1} - {no_of_af_lines}) × 2",'unit_price': self._get_clamp_price('Full Clamp', main_column_size),})
                    sequence += 10
        elif thick_config == '4':
            if thick_column_size:
                details.append({'sequence': sequence,'category': 'V SUPPORT TO MAIN COLUMN - FULL CLAMPS','component': 'Thick Column (All Sides)','clamp_type': 'Full Clamp','size': thick_column_size,'quantity': int((no_of_bays + 1) * 2),'formula': f"({no_of_bays + 1}) × 2 (All Columns)",'unit_price': self._get_clamp_price('Full Clamp', thick_column_size),})
                sequence += 10
        if no_of_spans > 1:
            if thick_config == '0':
                if no_of_af_lines > 0 and af_main_column_size:
                    af_half_qty = no_of_af_lines * (no_of_spans - 1)
                    details.append({'sequence': sequence,'category': 'V SUPPORT TO MAIN COLUMN - HALF CLAMPS','component': 'AF Main Column (Internal)','clamp_type': 'Half Clamp','size': af_main_column_size,'quantity': int(af_half_qty),'formula': f"{no_of_af_lines} × ({no_of_spans} - 1)",'unit_price': self._get_clamp_price('Half Clamp', af_main_column_size),})
                    sequence += 10
                if main_column_size:
                    main_half_qty = (no_of_bays + 1 - no_of_af_lines) * (no_of_spans - 1)
                    if main_half_qty > 0:
                        details.append({'sequence': sequence,'category': 'V SUPPORT TO MAIN COLUMN - HALF CLAMPS','component': 'Main Column (Internal)','clamp_type': 'Half Clamp','size': main_column_size,'quantity': int(main_half_qty),'formula': f"({no_of_bays + 1} - {no_of_af_lines}) × ({no_of_spans} - 1)",'unit_price': self._get_clamp_price('Half Clamp', main_column_size),})
                        sequence += 10
            elif thick_config == '1':
                if no_of_af_lines > 0 and af_main_column_size:
                    af_half_qty = no_of_af_lines * (no_of_spans - 1)
                    details.append({'sequence': sequence,'category': 'V SUPPORT TO MAIN COLUMN - HALF CLAMPS','component': 'AF Main Column (Internal)','clamp_type': 'Half Clamp','size': af_main_column_size,'quantity': int(af_half_qty),'formula': f"{no_of_af_lines} × ({no_of_spans} - 1)",'unit_price': self._get_clamp_price('Half Clamp', af_main_column_size),})
                    sequence += 10
                if main_column_size:
                    main_half_qty = (no_of_bays + 1 - no_of_af_lines) * (no_of_spans - 1)
                    if main_half_qty > 0:
                        details.append({'sequence': sequence,'category': 'V SUPPORT TO MAIN COLUMN - HALF CLAMPS','component': 'Main Column (Internal)','clamp_type': 'Half Clamp','size': main_column_size,'quantity': int(main_half_qty),'formula': f"({no_of_bays + 1} - {no_of_af_lines}) × ({no_of_spans} - 1)",'unit_price': self._get_clamp_price('Half Clamp', main_column_size),})
                        sequence += 10
            elif thick_config == '2':
                if thick_column_size:
                    total_half_qty = (no_of_bays + 1) * (no_of_spans - 1)
                    details.append({'sequence': sequence,'category': 'V SUPPORT TO MAIN COLUMN - HALF CLAMPS','component': 'Thick Column (Bay Side - Internal)','clamp_type': 'Half Clamp','size': thick_column_size,'quantity': int(total_half_qty),'formula': f"({no_of_bays + 1}) × ({no_of_spans} - 1)",'unit_price': self._get_clamp_price('Half Clamp', thick_column_size),})
                    sequence += 10
            elif thick_config == '3':
                if no_of_af_lines > 0 and af_main_column_size:
                    af_half_qty = no_of_af_lines * (no_of_spans - 1)
                    details.append({'sequence': sequence,'category': 'V SUPPORT TO MAIN COLUMN - HALF CLAMPS','component': 'AF Main Column (Internal)','clamp_type': 'Half Clamp','size': af_main_column_size,'quantity': int(af_half_qty),'formula': f"{no_of_af_lines} × ({no_of_spans} - 1)",'unit_price': self._get_clamp_price('Half Clamp', af_main_column_size),})
                    sequence += 10
                if main_column_size:
                    main_half_qty = (no_of_bays + 1 - no_of_af_lines) * (no_of_spans - 1)
                    if main_half_qty > 0:
                        details.append({'sequence': sequence,'category': 'V SUPPORT TO MAIN COLUMN - HALF CLAMPS','component': 'Main Column (Internal)','clamp_type': 'Half Clamp','size': main_column_size,'quantity': int(main_half_qty),'formula': f"({no_of_bays + 1} - {no_of_af_lines}) × ({no_of_spans} - 1)",'unit_price': self._get_clamp_price('Half Clamp', main_column_size),})
                        sequence += 10
            elif thick_config == '4':
                if thick_column_size:
                    total_half_qty = (no_of_bays + 1) * (no_of_spans - 1)
                    details.append({'sequence': sequence,'category': 'V SUPPORT TO MAIN COLUMN - HALF CLAMPS','component': 'Thick Column (All Sides - Internal)','clamp_type': 'Half Clamp','size': thick_column_size,'quantity': int(total_half_qty),'formula': f"({no_of_bays + 1}) × ({no_of_spans} - 1) = {no_of_bays + 1} × {no_of_spans - 1}",'unit_price': self._get_clamp_price('Half Clamp', thick_column_size),})
                    sequence += 10
        return details

    def _get_cross_bracing_details(self, sequence):
        details = []
        if self.front_back_c_c_cross_bracing_x:
            no_clamps = (self.no_of_spans + 1) * 4
            main_column_size = self._get_main_column_pipe_size()
            if main_column_size:
                details.append({'sequence': sequence,'category': 'FRONT/BACK CC CROSS BRACING','component': 'Main Column Clamps','clamp_type': 'Full Clamp','size': main_column_size,'quantity': int(no_clamps),'formula': f"({self.no_of_spans + 1}) × 4",'unit_price': self._get_clamp_price('Full Clamp', main_column_size),})
                sequence += 10
        if self.cross_bracing_column_arch:
            big_arch_size = self._get_big_arch_data()['size']
            small_arch_size = self._get_small_arch_data()['size']
            main_column_size = self._get_main_column_pipe_size()
            total_bracing = self.no_of_spans * 4
            if big_arch_size:
                details.append({'sequence': sequence,'category': 'COLUMN TO ARCH BRACING','component': 'Big Arch Clamps','clamp_type': 'Full Clamp','size': big_arch_size,'quantity': int(total_bracing / 2),'formula': f"{total_bracing} / 2 (half of total)",'unit_price': self._get_clamp_price('Full Clamp', big_arch_size),})
                sequence += 10
            if small_arch_size:
                details.append({'sequence': sequence,'category': 'COLUMN TO ARCH BRACING','component': 'Small Arch Clamps','clamp_type': 'Full Clamp','size': small_arch_size,'quantity': int(total_bracing / 2),'formula': f"{total_bracing} / 2 (half of total)",'unit_price': self._get_clamp_price('Full Clamp', small_arch_size),})
                sequence += 10
            if main_column_size:
                details.append({'sequence': sequence,'category': 'COLUMN TO ARCH BRACING','component': 'Main Column Clamps','clamp_type': 'Full Clamp','size': main_column_size,'quantity': int(total_bracing),'formula': f"Total = {total_bracing}",'unit_price': self._get_clamp_price('Full Clamp', main_column_size),})
                sequence += 10
        if self.cross_bracing_column_bottom:
            bottom_chord_size = self._get_bottom_chord_data()['size']
            main_column_size = self._get_main_column_pipe_size()
            total_bracing = self.no_of_spans * 4
            if bottom_chord_size:
                details.append({'sequence': sequence,'category': 'COLUMN TO BOTTOM BRACING','component': 'Bottom Chord Clamps','clamp_type': 'Full Clamp','size': bottom_chord_size,'quantity': int(total_bracing),'formula': f"Total = {total_bracing}",'unit_price': self._get_clamp_price('Full Clamp', bottom_chord_size),})
                sequence += 10
            if main_column_size:
                details.append({'sequence': sequence,'category': 'COLUMN TO BOTTOM BRACING','component': 'Main Column Clamps','clamp_type': 'Full Clamp','size': main_column_size,'quantity': int(total_bracing),'formula': f"Total = {total_bracing}",'unit_price': self._get_clamp_price('Full Clamp', main_column_size),})
        return details

    def _get_asc_support_details(self, sequence):
        details = []
        asc_support_count = self._get_asc_support_pipes_count()
        asc_pipe_size = self._get_asc_pipe_size()
        if asc_support_count > 0 and asc_pipe_size:
            details.append({'sequence': sequence,'category': 'ASC SUPPORT CLAMPS','component': 'Type A - ASC Pipes','clamp_type': 'Full Clamp','size': asc_pipe_size,'quantity': int(asc_support_count),'formula': f"Total ASC Support = {asc_support_count}",'unit_price': self._get_clamp_price('Full Clamp', asc_pipe_size),})
            sequence += 10
        column_clamps = self._calculate_asc_column_clamps()
        if column_clamps['thick_count'] > 0:
            thick_size = self._get_thick_column_pipe_size()
            if thick_size:
                details.append({'sequence': sequence,'category': 'ASC SUPPORT CLAMPS','component': 'Type B - Thick Columns','clamp_type': 'Full Clamp','size': thick_size,'quantity': int(column_clamps['thick_count']),'formula': f"Thick columns × Support/Hockey",'unit_price': self._get_clamp_price('Full Clamp', thick_size),})
                sequence += 10
        if column_clamps['middle_count'] > 0:
            middle_size = self._get_middle_column_pipe_size()
            if middle_size:
                details.append({'sequence': sequence,'category': 'ASC SUPPORT CLAMPS','component': 'Type B - Middle Columns','clamp_type': 'Full Clamp','size': middle_size,'quantity': int(column_clamps['middle_count']),'formula': f"Middle columns × Support/Hockey",'unit_price': self._get_clamp_price('Full Clamp', middle_size),})
                sequence += 10
        if column_clamps.get('af_main_count', 0) > 0:
            af_main_size = self._get_af_main_column_pipe_size()
            if af_main_size:
                details.append({'sequence': sequence,'category': 'ASC SUPPORT CLAMPS','component': 'Type B - AF Main Columns','clamp_type': 'Full Clamp','size': af_main_size,'quantity': int(column_clamps['af_main_count']),'formula': f"AF Main columns × Support/Hockey",'unit_price': self._get_clamp_price('Full Clamp', af_main_size),})
                sequence += 10
        if column_clamps['main_count'] > 0:
            main_size = self._get_main_column_pipe_size()
            if main_size:
                details.append({'sequence': sequence,'category': 'ASC SUPPORT CLAMPS','component': 'Type B - Main Columns','clamp_type': 'Full Clamp','size': main_size,'quantity': int(column_clamps['main_count']),'formula': f"Remaining ASC Support",'unit_price': self._get_clamp_price('Full Clamp', main_size),})
        return details

    def _get_asc_bracket_details(self, sequence):
        """Get ASC Bracket (F/Gutter Arch) clamp details for display"""
        details = []
        
        # Get configuration
        thick_config = self.thick_column
        no_of_spans = self.no_of_spans
        no_of_bays = self.no_of_bays
        no_af_lines = self.no_anchor_frame_lines
        no_big_column_per_af = int(self.no_column_big_frame) if self.no_column_big_frame else 0
        
        # Get pipe sizes
        thick_column_size = self._get_thick_column_pipe_size()
        main_column_size = self._get_main_column_pipe_size()
        af_main_column_size = self._get_af_main_column_pipe_size()
        big_column_size = self._get_big_column_pipe_size()
        
        # Check ASC existence
        has_front_span_asc = self.width_front_span_coridoor > 0
        has_back_span_asc = self.width_back_span_coridoor > 0
        has_front_bay_asc = self.width_front_bay_coridoor > 0
        has_back_bay_asc = self.width_back_bay_coridoor > 0
        
        # Determine bracket type
        if self.gutter_bracket_type == 'f_bracket':
            bracket_type = "F Bracket"
        elif self.gutter_bracket_type == 'arch':
            bracket_type = "Gutter Arch Bracket"
        else:
            return details  # No bracket type selected
        
        # Add header (optional - you can remove this if not needed)
        details.append({
            'sequence': sequence,
            'category': f'ASC BRACKET CLAMPS - {bracket_type}',
            'component': 'Configuration',
            'clamp_type': 'Info',
            'size': f'Thick Config: {thick_config}',
            'quantity': 0,
            'formula': f'Bay Side Clamp: {"Yes" if self.bay_side_clamp_required else "No"}',
            'unit_price': 0,
        })
        sequence += 10
        
        # FRONT SPAN ASC CALCULATIONS
        if has_front_span_asc:
            if thick_config in ['1', '2']:  # 4 Corner OR 2 Bay Side
                if thick_column_size:
                    details.append({
                        'sequence': sequence,
                        'category': 'ASC BRACKET - FRONT SPAN',
                        'component': 'Thick Columns',
                        'clamp_type': 'Full Clamp',
                        'size': thick_column_size,
                        'quantity': 2,
                        'formula': 'Fixed = 2',
                        'unit_price': self._get_clamp_price('Full Clamp', thick_column_size),
                    })
                    sequence += 10
                
                if no_af_lines >= 1:
                    if big_column_size and no_big_column_per_af > 0:
                        qty = no_of_spans * no_big_column_per_af
                        details.append({
                            'sequence': sequence,
                            'category': 'ASC BRACKET - FRONT SPAN',
                            'component': 'Big Columns',
                            'clamp_type': 'Full Clamp',
                            'size': big_column_size,
                            'quantity': qty,
                            'formula': f'{no_of_spans} × {no_big_column_per_af}',
                            'unit_price': self._get_clamp_price('Full Clamp', big_column_size),
                        })
                        sequence += 10
                    
                    if af_main_column_size:
                        details.append({
                            'sequence': sequence,
                            'category': 'ASC BRACKET - FRONT SPAN',
                            'component': 'AF Main Columns',
                            'clamp_type': 'Full Clamp',
                            'size': af_main_column_size,
                            'quantity': no_of_spans - 1,
                            'formula': f'{no_of_spans} - 1',
                            'unit_price': self._get_clamp_price('Full Clamp', af_main_column_size),
                        })
                        sequence += 10
                else:
                    if main_column_size:
                        details.append({
                            'sequence': sequence,
                            'category': 'ASC BRACKET - FRONT SPAN',
                            'component': 'Main Columns',
                            'clamp_type': 'Full Clamp',
                            'size': main_column_size,
                            'quantity': no_of_spans - 1,
                            'formula': f'{no_of_spans} - 1',
                            'unit_price': self._get_clamp_price('Full Clamp', main_column_size),
                        })
                        sequence += 10
            
            elif thick_config in ['3', '4']:  # 2 Span Side OR 4 Side
                if thick_column_size:
                    details.append({
                        'sequence': sequence,
                        'category': 'ASC BRACKET - FRONT SPAN',
                        'component': 'Thick Columns',
                        'clamp_type': 'Full Clamp',
                        'size': thick_column_size,
                        'quantity': no_of_spans + 1,
                        'formula': f'{no_of_spans} + 1',
                        'unit_price': self._get_clamp_price('Full Clamp', thick_column_size),
                    })
                    sequence += 10
                
                if no_af_lines >= 1 and big_column_size and no_big_column_per_af > 0:
                    qty = no_of_spans * no_big_column_per_af
                    details.append({
                        'sequence': sequence,
                        'category': 'ASC BRACKET - FRONT SPAN',
                        'component': 'Big Columns',
                        'clamp_type': 'Full Clamp',
                        'size': big_column_size,
                        'quantity': qty,
                        'formula': f'{no_of_spans} × {no_big_column_per_af}',
                        'unit_price': self._get_clamp_price('Full Clamp', big_column_size),
                    })
                    sequence += 10
            
            else:  # thick_config == '0'
                if no_af_lines >= 1:
                    if big_column_size and no_big_column_per_af > 0:
                        qty = no_of_spans * no_big_column_per_af
                        details.append({
                            'sequence': sequence,
                            'category': 'ASC BRACKET - FRONT SPAN',
                            'component': 'Big Columns',
                            'clamp_type': 'Full Clamp',
                            'size': big_column_size,
                            'quantity': qty,
                            'formula': f'{no_of_spans} × {no_big_column_per_af}',
                            'unit_price': self._get_clamp_price('Full Clamp', big_column_size),
                        })
                        sequence += 10
                    
                    if af_main_column_size:
                        details.append({
                            'sequence': sequence,
                            'category': 'ASC BRACKET - FRONT SPAN',
                            'component': 'AF Main Columns',
                            'clamp_type': 'Full Clamp',
                            'size': af_main_column_size,
                            'quantity': no_of_spans + 1,
                            'formula': f'{no_of_spans} + 1',
                            'unit_price': self._get_clamp_price('Full Clamp', af_main_column_size),
                        })
                        sequence += 10
                else:
                    if main_column_size:
                        details.append({
                            'sequence': sequence,
                            'category': 'ASC BRACKET - FRONT SPAN',
                            'component': 'Main Columns',
                            'clamp_type': 'Full Clamp',
                            'size': main_column_size,
                            'quantity': no_of_spans + 1,
                            'formula': f'{no_of_spans} + 1',
                            'unit_price': self._get_clamp_price('Full Clamp', main_column_size),
                        })
                        sequence += 10
        
        # BACK SPAN ASC CALCULATIONS
        if has_back_span_asc:
            if thick_config in ['1', '2']:  # 4 Corner OR 2 Bay Side
                if thick_column_size:
                    details.append({
                        'sequence': sequence,
                        'category': 'ASC BRACKET - BACK SPAN',
                        'component': 'Thick Columns',
                        'clamp_type': 'Full Clamp',
                        'size': thick_column_size,
                        'quantity': 2,
                        'formula': 'Fixed = 2',
                        'unit_price': self._get_clamp_price('Full Clamp', thick_column_size),
                    })
                    sequence += 10
                
                if no_af_lines >= 2:  # Note: >= 2 for Back Span
                    if big_column_size and no_big_column_per_af > 0:
                        qty = no_of_spans * no_big_column_per_af
                        details.append({
                            'sequence': sequence,
                            'category': 'ASC BRACKET - BACK SPAN',
                            'component': 'Big Columns',
                            'clamp_type': 'Full Clamp',
                            'size': big_column_size,
                            'quantity': qty,
                            'formula': f'{no_of_spans} × {no_big_column_per_af}',
                            'unit_price': self._get_clamp_price('Full Clamp', big_column_size),
                        })
                        sequence += 10
                    
                    if af_main_column_size:
                        details.append({
                            'sequence': sequence,
                            'category': 'ASC BRACKET - BACK SPAN',
                            'component': 'AF Main Columns',
                            'clamp_type': 'Full Clamp',
                            'size': af_main_column_size,
                            'quantity': no_of_spans - 1,
                            'formula': f'{no_of_spans} - 1',
                            'unit_price': self._get_clamp_price('Full Clamp', af_main_column_size),
                        })
                        sequence += 10
                else:
                    if main_column_size:
                        details.append({
                            'sequence': sequence,
                            'category': 'ASC BRACKET - BACK SPAN',
                            'component': 'Main Columns',
                            'clamp_type': 'Full Clamp',
                            'size': main_column_size,
                            'quantity': no_of_spans - 1,
                            'formula': f'{no_of_spans} - 1',
                            'unit_price': self._get_clamp_price('Full Clamp', main_column_size),
                        })
                        sequence += 10
            
            elif thick_config in ['3', '4']:  # 2 Span Side OR 4 Side
                if thick_column_size:
                    details.append({
                        'sequence': sequence,
                        'category': 'ASC BRACKET - BACK SPAN',
                        'component': 'Thick Columns',
                        'clamp_type': 'Full Clamp',
                        'size': thick_column_size,
                        'quantity': no_of_spans + 1,
                        'formula': f'{no_of_spans} + 1',
                        'unit_price': self._get_clamp_price('Full Clamp', thick_column_size),
                    })
                    sequence += 10
                
                if no_af_lines >= 2 and big_column_size and no_big_column_per_af > 0:
                    qty = no_of_spans * no_big_column_per_af
                    details.append({
                        'sequence': sequence,
                        'category': 'ASC BRACKET - BACK SPAN',
                        'component': 'Big Columns',
                        'clamp_type': 'Full Clamp',
                        'size': big_column_size,
                        'quantity': qty,
                        'formula': f'{no_of_spans} × {no_big_column_per_af}',
                        'unit_price': self._get_clamp_price('Full Clamp', big_column_size),
                    })
                    sequence += 10
            
            else:  # thick_config == '0'
                if no_af_lines >= 2:
                    if big_column_size and no_big_column_per_af > 0:
                        qty = no_of_spans * no_big_column_per_af
                        details.append({
                            'sequence': sequence,
                            'category': 'ASC BRACKET - BACK SPAN',
                            'component': 'Big Columns',
                            'clamp_type': 'Full Clamp',
                            'size': big_column_size,
                            'quantity': qty,
                            'formula': f'{no_of_spans} × {no_big_column_per_af}',
                            'unit_price': self._get_clamp_price('Full Clamp', big_column_size),
                        })
                        sequence += 10
                    
                    if af_main_column_size:
                        details.append({
                            'sequence': sequence,
                            'category': 'ASC BRACKET - BACK SPAN',
                            'component': 'AF Main Columns',
                            'clamp_type': 'Full Clamp',
                            'size': af_main_column_size,
                            'quantity': no_of_spans + 1,
                            'formula': f'{no_of_spans} + 1',
                            'unit_price': self._get_clamp_price('Full Clamp', af_main_column_size),
                        })
                        sequence += 10
                else:
                    if main_column_size:
                        details.append({
                            'sequence': sequence,
                            'category': 'ASC BRACKET - BACK SPAN',
                            'component': 'Main Columns',
                            'clamp_type': 'Full Clamp',
                            'size': main_column_size,
                            'quantity': no_of_spans + 1,
                            'formula': f'{no_of_spans} + 1',
                            'unit_price': self._get_clamp_price('Full Clamp', main_column_size),
                        })
                        sequence += 10
        
        # BAY ASC CALCULATIONS (only if Gutter Arch and Bay Side Clamp Required = Yes)
        if self.gutter_bracket_type == 'arch' and self.bay_side_clamp_required:
            
            # FRONT BAY ASC
            if has_front_bay_asc:
                if thick_config in ['1', '3']:  # 4 Corner OR 2 Span Side
                    if thick_column_size:
                        details.append({
                            'sequence': sequence,
                            'category': 'ASC BRACKET - FRONT BAY',
                            'component': 'Thick Columns',
                            'clamp_type': 'Full Clamp',
                            'size': thick_column_size,
                            'quantity': 2,
                            'formula': 'Fixed = 2',
                            'unit_price': self._get_clamp_price('Full Clamp', thick_column_size),
                        })
                        sequence += 10
                    
                    if main_column_size:
                        details.append({
                            'sequence': sequence,
                            'category': 'ASC BRACKET - FRONT BAY',
                            'component': 'Main Columns',
                            'clamp_type': 'Full Clamp',
                            'size': main_column_size,
                            'quantity': no_of_bays - 1,
                            'formula': f'{no_of_bays} - 1',
                            'unit_price': self._get_clamp_price('Full Clamp', main_column_size),
                        })
                        sequence += 10
                        
                elif thick_config in ['2', '4']:  # 2 Bay Side OR 4 Side
                    if thick_column_size:
                        details.append({
                            'sequence': sequence,
                            'category': 'ASC BRACKET - FRONT BAY',
                            'component': 'Thick Columns',
                            'clamp_type': 'Full Clamp',
                            'size': thick_column_size,
                            'quantity': no_of_bays + 1,
                            'formula': f'{no_of_bays} + 1',
                            'unit_price': self._get_clamp_price('Full Clamp', thick_column_size),
                        })
                        sequence += 10
                        
                else:  # thick_config == '0'
                    if main_column_size:
                        details.append({
                            'sequence': sequence,
                            'category': 'ASC BRACKET - FRONT BAY',
                            'component': 'Main Columns',
                            'clamp_type': 'Full Clamp',
                            'size': main_column_size,
                            'quantity': no_of_bays + 1,
                            'formula': f'{no_of_bays} + 1',
                            'unit_price': self._get_clamp_price('Full Clamp', main_column_size),
                        })
                        sequence += 10
            
            # BACK BAY ASC
            if has_back_bay_asc:
                if thick_config in ['1', '3']:  # 4 Corner OR 2 Span Side
                    if thick_column_size:
                        details.append({
                            'sequence': sequence,
                            'category': 'ASC BRACKET - BACK BAY',
                            'component': 'Thick Columns',
                            'clamp_type': 'Full Clamp',
                            'size': thick_column_size,
                            'quantity': 2,
                            'formula': 'Fixed = 2',
                            'unit_price': self._get_clamp_price('Full Clamp', thick_column_size),
                        })
                        sequence += 10
                    
                    if main_column_size:
                        details.append({
                            'sequence': sequence,
                            'category': 'ASC BRACKET - BACK BAY',
                            'component': 'Main Columns',
                            'clamp_type': 'Full Clamp',
                            'size': main_column_size,
                            'quantity': no_of_bays - 1,
                            'formula': f'{no_of_bays} - 1',
                            'unit_price': self._get_clamp_price('Full Clamp', main_column_size),
                        })
                        sequence += 10
                        
                elif thick_config in ['2', '4']:  # 2 Bay Side OR 4 Side
                    if thick_column_size:
                        details.append({
                            'sequence': sequence,
                            'category': 'ASC BRACKET - BACK BAY',
                            'component': 'Thick Columns',
                            'clamp_type': 'Full Clamp',
                            'size': thick_column_size,
                            'quantity': no_of_bays + 1,
                            'formula': f'{no_of_bays} + 1',
                            'unit_price': self._get_clamp_price('Full Clamp', thick_column_size),
                        })
                        sequence += 10
                        
                else:  # thick_config == '0'
                    if main_column_size:
                        details.append({
                            'sequence': sequence,
                            'category': 'ASC BRACKET - BACK BAY',
                            'component': 'Main Columns',
                            'clamp_type': 'Full Clamp',
                            'size': main_column_size,
                            'quantity': no_of_bays + 1,
                            'formula': f'{no_of_bays} + 1',
                            'unit_price': self._get_clamp_price('Full Clamp', main_column_size),
                        })
                        sequence += 10
        
        return details

    def _get_border_purlin_details(self, sequence):
        details = []
        if int(self.bay_side_border_purlin) > 0:
            details.extend(self._get_bay_side_border_details(sequence))
            sequence += 50
        if int(self.span_side_border_purlin) > 0:
            details.extend(self._get_span_side_border_details(sequence))
            sequence += 50
        if self.no_anchor_frame_lines >= 1 and int(self.span_side_border_purlin) > 0:
            details.extend(self._get_anchor_frame_details(sequence))
        return details

    def _get_bay_side_border_details(self, sequence):
        details = []
        bay_side_value = int(self.bay_side_border_purlin)
        if self.width_front_bay_coridoor > 0:
            pipe_size = self._get_asc_pipe_size()
            if pipe_size:
                half_qty = (self.no_of_bays - 1) * bay_side_value
                details.append({'sequence': sequence,'category': 'BORDER PURLIN - BAY SIDE','component': 'Front Bay (ASC)','clamp_type': 'Half Clamp','size': pipe_size,'quantity': int(half_qty),'formula': f"({self.no_of_bays} - 1) × {bay_side_value}",'unit_price': self._get_clamp_price('Half Clamp', pipe_size),})
                sequence += 10
                full_qty = 2 * bay_side_value
                details.append({'sequence': sequence,'category': 'BORDER PURLIN - BAY SIDE','component': 'Front Bay (ASC)','clamp_type': 'Full Clamp','size': pipe_size,'quantity': int(full_qty),'formula': f"2 × {bay_side_value}",'unit_price': self._get_clamp_price('Full Clamp', pipe_size),})
                sequence += 10
        else:
            half_size, full_size = self._get_bay_side_pipe_sizes('front')
            if half_size and full_size:
                half_qty = (self.no_of_bays - 1) * bay_side_value
                details.append({'sequence': sequence,'category': 'BORDER PURLIN - BAY SIDE','component': f'Front Bay (Thick Config: {self.thick_column})','clamp_type': 'Half Clamp','size': half_size,'quantity': int(half_qty),'formula': f"({self.no_of_bays} - 1) × {bay_side_value}",'unit_price': self._get_clamp_price('Half Clamp', half_size),})
                sequence += 10
                full_qty = 2 * bay_side_value
                details.append({'sequence': sequence,'category': 'BORDER PURLIN - BAY SIDE','component': f'Front Bay (Thick Config: {self.thick_column})','clamp_type': 'Full Clamp','size': full_size,'quantity': int(full_qty),'formula': f"2 × {bay_side_value}",'unit_price': self._get_clamp_price('Full Clamp', full_size),})
                sequence += 10
        return details

    def _get_span_side_border_details(self, sequence):
        details = []
        return details

    def _get_anchor_frame_details(self, sequence):
        details = []
        span_side_value = int(self.span_side_border_purlin)
        if span_side_value <= 0 or self.no_anchor_frame_lines <= 0:
            return details
        if self.no_anchor_frame_lines == 1:
            has_asc = self.width_front_span_coridoor > 0 or self.width_back_span_coridoor > 0
            pipe_size = self._get_asc_pipe_size() if has_asc else self._get_big_column_pipe_size()
            if pipe_size:
                half_qty = self.no_of_spans * span_side_value
                details.append({'sequence': sequence,'category': 'ANCHOR FRAME LINES','component': 'Single Anchor Frame Line','clamp_type': 'Half Clamp','size': pipe_size,'quantity': int(half_qty),'formula': f"{self.no_of_spans} × {span_side_value}",'unit_price': self._get_clamp_price('Half Clamp', pipe_size),})
        elif self.no_anchor_frame_lines >= 2:
            if self.width_front_span_coridoor > 0:
                pipe_size = self._get_asc_pipe_size()
            else:
                pipe_size = self._get_big_column_pipe_size()
            if pipe_size:
                half_qty = self.no_of_spans * span_side_value
                details.append({'sequence': sequence,'category': 'ANCHOR FRAME LINES','component': 'Front Span Anchor Frame','clamp_type': 'Half Clamp','size': pipe_size,'quantity': int(half_qty),'formula': f"{self.no_of_spans} × {span_side_value}",'unit_price': self._get_clamp_price('Half Clamp', pipe_size),})
                sequence += 10
            if self.width_back_span_coridoor > 0:
                pipe_size = self._get_asc_pipe_size()
            else:
                pipe_size = self._get_big_column_pipe_size()
            if pipe_size:
                half_qty = self.no_of_spans * span_side_value
                details.append({'sequence': sequence,'category': 'ANCHOR FRAME LINES','component': 'Back Span Anchor Frame','clamp_type': 'Half Clamp','size': pipe_size,'quantity': int(half_qty),'formula': f"{self.no_of_spans} × {span_side_value}",'unit_price': self._get_clamp_price('Half Clamp', pipe_size),})
        return details

    def _get_arch_middle_purlin_details(self, sequence):
        details = []
        if self.arch_middle_purlin_big_arch != '0' and int(self.arch_middle_purlin_big_arch_pcs) > 0:
            details.extend(self._get_big_arch_middle_purlin_details(sequence))
            sequence += 50
        if self.arch_middle_purlin_small_arch != '0' and int(self.arch_middle_purlin_small_arch_pcs) > 0:
            details.extend(self._get_small_arch_middle_purlin_details(sequence))
        return details

    def _get_big_arch_middle_purlin_details(self, sequence):
        details = []
        config_value = self.arch_middle_purlin_big_arch
        pcs_value = int(self.arch_middle_purlin_big_arch_pcs)
        no_arch_middle_purlin_big_arch = 0
        arch_middle_purlin = self.lower_component_ids.filtered(lambda c: c.name == 'Arch Middle Purlin Big Arch')
        if arch_middle_purlin:
            no_arch_middle_purlin_big_arch = arch_middle_purlin.nos
        big_arch_size = self._get_big_arch_data()['size']
        if not big_arch_size or no_arch_middle_purlin_big_arch == 0:
            return details
        full_qty = 0
        full_formula = ""
        if config_value == '1':
            full_qty = no_arch_middle_purlin_big_arch * 2
            full_formula = f"{no_arch_middle_purlin_big_arch} × 2"
        elif config_value == '2':
            full_qty = no_arch_middle_purlin_big_arch * 2
            full_formula = f"{no_arch_middle_purlin_big_arch} × 2"
        elif config_value == '3':
            full_qty = 4 * pcs_value
            full_formula = f"4 × {pcs_value}"
        elif config_value == '4':
            full_qty = ((((self.no_of_spans - 2) * 4) + 4) * pcs_value)
            full_formula = f"(((({self.no_of_spans} - 2) × 4) + 4) × {pcs_value})"
        elif config_value == '5':
            full_qty = self.no_of_spans * 2
            full_formula = f"{self.no_of_spans} × 2"
        if full_qty > 0:
            config_name = dict(self._fields['arch_middle_purlin_big_arch'].selection)[config_value]
            details.append({'sequence': sequence,'category': 'ARCH MIDDLE PURLIN - BIG ARCH','component': f'Full Clamps ({config_name})','clamp_type': 'Full Clamp','size': big_arch_size,'quantity': int(full_qty),'formula': full_formula,'unit_price': self._get_clamp_price('Full Clamp', big_arch_size),})
            sequence += 10
        half_qty = 0
        half_formula = ""
        if config_value == '3':
            half_qty = (no_arch_middle_purlin_big_arch * 2) - (4 * pcs_value)
            half_formula = f"({no_arch_middle_purlin_big_arch} × 2) - (4 × {pcs_value})"
        elif config_value == '4':
            half_qty = no_arch_middle_purlin_big_arch - (((((self.no_of_spans - 2) * 4) + 4) * pcs_value) / 2)
            half_formula = f"{no_arch_middle_purlin_big_arch} - ((((({self.no_of_spans} - 2) × 4) + 4) × {pcs_value}) / 2)"
        elif config_value == '5':
            half_qty = self.no_of_spans * (self.no_of_bays - 1)
            half_formula = f"{self.no_of_spans} × ({self.no_of_bays} - 1)"
        if half_qty > 0:
            config_name = dict(self._fields['arch_middle_purlin_big_arch'].selection)[config_value]
            details.append({'sequence': sequence,'category': 'ARCH MIDDLE PURLIN - BIG ARCH','component': f'Half Clamps ({config_name})','clamp_type': 'Half Clamp','size': big_arch_size,'quantity': int(half_qty),'formula': half_formula,'unit_price': self._get_clamp_price('Half Clamp', big_arch_size),})
        return details

    def _get_small_arch_middle_purlin_details(self, sequence):
        details = []
        config_value = self.arch_middle_purlin_small_arch
        pcs_value = int(self.arch_middle_purlin_small_arch_pcs)
        no_arch_middle_purlin_small_arch = 0
        arch_middle_purlin = self.lower_component_ids.filtered(lambda c: c.name == 'Arch Middle Purlin Small Arch')
        if arch_middle_purlin:
            no_arch_middle_purlin_small_arch = arch_middle_purlin.nos
        small_arch_size = self._get_small_arch_data()['size']
        if not small_arch_size or no_arch_middle_purlin_small_arch == 0:
            return details
        full_qty = 0
        full_formula = ""
        if config_value == '1':
            full_qty = no_arch_middle_purlin_small_arch * 2
            full_formula = f"{no_arch_middle_purlin_small_arch} × 2"
        elif config_value == '2':
            full_qty = no_arch_middle_purlin_small_arch * 2
            full_formula = f"{no_arch_middle_purlin_small_arch} × 2"
        elif config_value == '3':
            full_qty = 4 * pcs_value
            full_formula = f"4 × {pcs_value}"
        elif config_value == '4':
            full_qty = ((((self.no_of_spans - 2) * 4) + 4) * pcs_value)
            full_formula = f"(((({self.no_of_spans} - 2) × 4) + 4) × {pcs_value})"
        elif config_value == '5':
            full_qty = self.no_of_spans * 2
            full_formula = f"{self.no_of_spans} × 2"
        if full_qty > 0:
            config_name = dict(self._fields['arch_middle_purlin_small_arch'].selection)[config_value]
            details.append({'sequence': sequence,'category': 'ARCH MIDDLE PURLIN - SMALL ARCH','component': f'Full Clamps ({config_name})','clamp_type': 'Full Clamp','size': small_arch_size,'quantity': int(full_qty),'formula': full_formula,'unit_price': self._get_clamp_price('Full Clamp', small_arch_size),})
            sequence += 10
        half_qty = 0
        half_formula = ""
        if config_value == '3':
            half_qty = (no_arch_middle_purlin_small_arch * 2) - (4 * pcs_value)
            half_formula = f"({no_arch_middle_purlin_small_arch} × 2) - (4 × {pcs_value})"
        elif config_value == '4':
            half_qty = no_arch_middle_purlin_small_arch - (((((self.no_of_spans - 2) * 4) + 4) * pcs_value) / 2)
            half_formula = f"{no_arch_middle_purlin_small_arch} - ((((({self.no_of_spans} - 2) × 4) + 4) × {pcs_value}) / 2)"
        elif config_value == '5':
            half_qty = self.no_of_spans * (self.no_of_bays - 1)
            half_formula = f"{self.no_of_spans} × ({self.no_of_bays} - 1)"
        if half_qty > 0:
            config_name = dict(self._fields['arch_middle_purlin_small_arch'].selection)[config_value]
            details.append({'sequence': sequence,'category': 'ARCH MIDDLE PURLIN - SMALL ARCH','component': f'Half Clamps ({config_name})','clamp_type': 'Half Clamp','size': small_arch_size,'quantity': int(half_qty),'formula': half_formula,'unit_price': self._get_clamp_price('Half Clamp', small_arch_size),})
        return details
        
    def _get_af_main_column_pipe_size(self):
        af_main_columns = self.frame_component_ids.filtered(lambda c: c.name == 'AF Main Columns')
        if af_main_columns and af_main_columns.pipe_id and af_main_columns.pipe_id.pipe_size:
            return f"{af_main_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return self._get_main_column_pipe_size()
    
    def _get_clamp_price(self, clamp_type, size):
        master_record = self.env['accessories.master'].search([('name', '=', clamp_type),('category', '=', 'clamps'),('size_specification', '=', size),('active', '=', True)], limit=1)
        return master_record.unit_price if master_record else 0.0
    
    def _get_bay_side_pipe_sizes(self, location='front'):
        try:
            thick_config = self.thick_column
            if thick_config == '1':
                half_size = self._get_main_column_pipe_size()
                full_size = self._get_thick_column_pipe_size()
            elif thick_config in ['2', '4']:
                half_size = self._get_thick_column_pipe_size()
                full_size = self._get_thick_column_pipe_size()
            else:
                half_size = self._get_main_column_pipe_size()
                full_size = self._get_main_column_pipe_size()
            return half_size, full_size
        except Exception as e:
            _logger.error(f"Error determining bay side pipe sizes: {e}")
            return None, None
    
    def _get_span_side_pipe_sizes(self, location='front'):
        try:
            thick_config = self.thick_column
            if thick_config == '1':
                half_size = self._get_main_column_pipe_size()
                full_size = self._get_thick_column_pipe_size()
            elif thick_config in ['3', '4']:
                half_size = self._get_thick_column_pipe_size()
                full_size = self._get_thick_column_pipe_size()
            else:
                half_size = self._get_main_column_pipe_size()
                full_size = self._get_main_column_pipe_size()
            return half_size, full_size
        except Exception as e:
            _logger.error(f"Error determining span side pipe sizes: {e}")
            return None, None
    
    def _get_front_bay_hockey_count(self):
        try:
            if self.width_front_bay_coridoor > 0:
                return (self.span_length / self.bay_width) + 1
            return 0
        except Exception:
            return 0
    
    def _get_back_bay_hockey_count(self):
        try:
            if self.width_back_bay_coridoor > 0:
                return (self.span_length / self.bay_width) + 1
            return 0
        except Exception:
            return 0
    
    def _get_front_span_hockey_count(self):
        try:
            if self.width_front_span_coridoor > 0:
                big_frame = int(self.no_column_big_frame) + 1
                return ((self.bay_length / self.span_width) * big_frame) + 1
            return 0
        except Exception:
            return 0
    
    def _get_back_span_hockey_count(self):
        try:
            if self.width_back_span_coridoor > 0:
                big_frame = int(self.no_column_big_frame) + 1
                return ((self.bay_length / self.span_width) * big_frame) + 1
            return 0
        except Exception:
            return 0
    
    def _get_big_column_pipe_size(self):
        try:
            middle_columns = self.frame_component_ids.filtered(lambda c: c.name == 'Middle Columns')
            if middle_columns and middle_columns.pipe_id and middle_columns.pipe_id.pipe_size:
                return f"{middle_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
            quadruple_columns = self.frame_component_ids.filtered(lambda c: c.name == 'Quadruple Columns')
            if quadruple_columns and quadruple_columns.pipe_id and quadruple_columns.pipe_id.pipe_size:
                return f"{quadruple_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
            return self._get_main_column_pipe_size()
        except Exception as e:
            _logger.error(f"Error getting big column pipe size: {e}")
            return None

    def _add_to_clamp_accumulator(self, accumulator, clamp_type, size, quantity):
        if quantity <= 0:
            return
        key = (clamp_type, size)
        if key in accumulator:
            accumulator[key] += quantity
        else:
            accumulator[key] = quantity

    def _create_clamp_components_from_accumulator(self, accumulator):
        for (clamp_type, size), quantity in accumulator.items():
            master_record = self.env['accessories.master'].search([('name', '=', clamp_type),('category', '=', 'clamps'),('size_specification', '=', size),('active', '=', True)], limit=1)
            unit_price = master_record.unit_price if master_record else 0.0
            component_name = f"{clamp_type} - {size}"
            vals = {'green_master_id': self.id,'section': 'clamps','name': component_name,'nos': int(quantity),'size_specification': size,'unit_price': unit_price,'is_calculated': True,'description': f"Auto-calculated {clamp_type} for {size} pipes",}
            if master_record:
                vals['accessories_master_id'] = master_record.id
            self.env['accessories.component.line'].create(vals)
    
    def _create_accessory_component(self, section, name, nos, size_spec, custom_unit_price=None):
        try:
            if nos <= 0:
                return None
            if custom_unit_price is not None:
                unit_price = custom_unit_price
            else:
                master_record = self.env['accessories.master'].search([('name', '=', name),('category', '=', section),('active', '=', True)], limit=1)
                unit_price = master_record.unit_price if master_record else 0.0
            vals = {'green_master_id': self.id,'section': section,'name': name,'nos': int(nos),'size_specification': size_spec,'unit_price': unit_price,'is_calculated': True,'description': f"Auto-calculated accessory for {section} section",}
            if custom_unit_price is None:
                master_record = self.env['accessories.master'].search([('name', '=', name),('category', '=', section),('active', '=', True)], limit=1)
                if master_record:
                    vals['accessories_master_id'] = master_record.id
            component = self.env['accessories.component.line'].create(vals)
            if 'Clamps' in name and section == 'clamps':
                component.auto_detected_size = size_spec
            return component
        except Exception as e:
            _logger.error(f"Error creating accessory component {name}: {e}")
            return None
    
    def _get_big_arch_count(self):
        big_arch_component = self.truss_component_ids.filtered(lambda c: c.name == 'Big Arch')
        return big_arch_component.nos if big_arch_component else 0
    
    def _get_small_arch_count(self):
        small_arch_component = self.truss_component_ids.filtered(lambda c: c.name == 'Small Arch')
        return small_arch_component.nos if small_arch_component else 0
    
    def _get_middle_columns_count(self):
        middle_columns = self.frame_component_ids.filtered(lambda c: c.name in ['Middle Columns', 'Quadruple Columns'])
        if middle_columns:
            return middle_columns[0].nos
        if hasattr(self, 'no_column_big_frame') and self.no_column_big_frame:
            if self.no_column_big_frame == '1':
                return self.no_anchor_frame_lines * self.no_of_spans
            elif self.no_column_big_frame in ['2', '3']:
                return self.no_anchor_frame_lines * self.no_of_spans * 2
        return 0
    
    def _get_foundations_count(self):
        total_foundations = 0
        foundation_components = self.frame_component_ids.filtered(lambda c: 'Foundations' in c.name and 'Columns' in c.name)
        for component in foundation_components:
            total_foundations += component.nos
        return total_foundations

    def _get_asc_pipes_count(self):
        total_asc_pipes = 0
        asc_components = self.asc_component_ids.filtered(lambda c: 'ASC Pipes' in c.name)
        for component in asc_components:
            total_asc_pipes += component.nos
        return total_asc_pipes
    
    def _get_asc_support_pipes_count(self):
        asc_support = self.asc_component_ids.filtered(lambda c: c.name == 'ASC Pipe Support')
        return asc_support.nos if asc_support else 0
        
    def _get_asc_pipe_size(self):
        asc_pipes = self.asc_component_ids.filtered(lambda c: 'ASC Pipes' in c.name)
        if asc_pipes and asc_pipes[0].pipe_id and asc_pipes[0].pipe_id.pipe_size:
            return f"{asc_pipes[0].pipe_id.pipe_size.size_in_mm:.0f}mm"
        return None

    def _get_thick_column_pipe_size(self):
        thick_columns = self.frame_component_ids.filtered(lambda c: c.name == 'Thick Columns')
        if thick_columns and thick_columns.pipe_id and thick_columns.pipe_id.pipe_size:
            return f"{thick_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return None

    def _get_main_column_pipe_size(self):
        main_columns = self.frame_component_ids.filtered(lambda c: c.name == 'Main Columns')
        if main_columns and main_columns.pipe_id and main_columns.pipe_id.pipe_size:
            return f"{main_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return None

    def _get_middle_column_pipe_size(self):
        middle_columns = self.frame_component_ids.filtered(lambda c: c.name in ['Middle Columns', 'Quadruple Columns'])
        if middle_columns and middle_columns[0].pipe_id and middle_columns[0].pipe_id.pipe_size:
            return f"{middle_columns[0].pipe_id.pipe_size.size_in_mm:.0f}mm"
        return None
    
    def _get_bottom_chord_data(self):
        bottom_chord_components = self.truss_component_ids.filtered(lambda c: 'Bottom Chord' in c.name and 'Female' not in c.name and 'V Support' not in c.name)
        data = {'count': 0, 'size': None, 'afs_count': 0}
        if bottom_chord_components:
            data['count'] = sum(bottom_chord_components.mapped('nos'))
            for component in bottom_chord_components:
                if component.pipe_id and component.pipe_id.pipe_size:
                    data['size'] = f"{component.pipe_id.pipe_size.size_in_mm:.0f}mm"
                    break
        anchor_frame_singular = self.truss_component_ids.filtered(lambda c: c.name == 'Bottom Chord Anchor Frame Singular')
        if anchor_frame_singular:
            data['afs_count'] = anchor_frame_singular.nos
        return data

    def _get_v_support_count(self):
        v_support = self.truss_component_ids.filtered(lambda c: c.name == 'V Support Bottom Chord')
        return v_support.nos if v_support else 0

    def _get_big_arch_data(self):
        big_arch = self.truss_component_ids.filtered(lambda c: c.name == 'Big Arch')
        data = {'count': 0, 'size': None}
        if big_arch:
            data['count'] = big_arch.nos
            if big_arch.pipe_id and big_arch.pipe_id.pipe_size:
                data['size'] = f"{big_arch.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return data

    def _get_small_arch_data(self):
        small_arch = self.truss_component_ids.filtered(lambda c: c.name == 'Small Arch')
        data = {'count': 0, 'size': None}
        if small_arch:
            data['count'] = small_arch.nos
            if small_arch.pipe_id and small_arch.pipe_id.pipe_size:
                data['size'] = f"{small_arch.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return data

    def _get_vent_support_big_arch_count(self):
        vent_support = self.truss_component_ids.filtered(lambda c: c.name == 'Vent Support for Big Arch')
        return vent_support.nos if vent_support else 0

    def _get_arch_support_straight_middle_data(self):
        arch_support = self.truss_component_ids.filtered(lambda c: c.name == 'Arch Support Straight Middle')
        data = {'count': 0, 'size': None}
        if arch_support:
            data['count'] = arch_support.nos
            if arch_support.pipe_id and arch_support.pipe_id.pipe_size:
                data['size'] = f"{arch_support.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return data

    def _get_middle_column_data(self):
        middle_columns = self.frame_component_ids.filtered(lambda c: c.name == 'Middle Columns')
        data = {'count': 0, 'size': None}
        if middle_columns:
            data['count'] = middle_columns.nos
            if middle_columns.pipe_id and middle_columns.pipe_id.pipe_size:
                data['size'] = f"{middle_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return data
    
    def _save_accessories_selections(self):
        saved_selections = {}
        for component in self.accessories_component_ids:
            key = f"{component.section}_{component.name}"
            saved_selections[key] = {'unit_price': component.unit_price,'size_override': component.size_override,'manual_size': component.manual_size,'notes': component.notes or '','accessories_master_id': component.accessories_master_id.id if component.accessories_master_id else False,}
        return saved_selections
    
    def _restore_accessories_selections(self, saved_selections):
        if not saved_selections:
            return
        for component in self.accessories_component_ids:
            key = f"{component.section}_{component.name}"
            if key in saved_selections:
                selection_data = saved_selections[key]
                try:
                    component.write({'unit_price': selection_data['unit_price'],'size_override': selection_data['size_override'],'manual_size': selection_data['manual_size'],'notes': selection_data['notes'],'accessories_master_id': selection_data['accessories_master_id'],})
                except Exception as e:
                    _logger.error(f"Failed to restore accessory selection for {component.name}: {e}")
    
    def action_calculate_accessories(self):
        for record in self:
            try:
                record._calculate_all_accessories()
                message = f'''ACCESSORIES CALCULATION COMPLETED:\n\n🔧 Brackets: {record.total_brackets_cost:.2f}\n🔗 Wires & Connectors: {record.total_wires_connectors_cost:.2f}\n🛠️ Clamps: {record.total_clamps_cost:.2f}\n\n📊 TOTAL ACCESSORIES: {record.total_accessories_cost:.2f}\n💰 NEW GRAND TOTAL: {record.grand_total_cost:.2f}\n\nComponents generated: {len(record.accessories_component_ids)}'''
                return {'type': 'ir.actions.client','tag': 'display_notification','params': {'title': 'Accessories Calculated Successfully','message': message,'type': 'success','sticky': True,}}
            except Exception as e:
                _logger.error(f"Error in accessories calculation: {e}")
                return {'type': 'ir.actions.client','tag': 'display_notification','params': {'title': 'Accessories Calculation Error','message': f'Error occurred: {str(e)}','type': 'danger',}}
    
    def action_calculate_profiles(self):
        for record in self:
            try:
                record._compute_all_profiles()
                message = f'''PROFILE CALCULATION BREAKDOWN:\n\n🏗️ Profiles For Arch: {record.profiles_for_arch:.2f}m\n📏 Profile For Purlin: {record.profile_for_purlin:.2f}m\n⬇️ Profile for Bottom: {record.profile_for_bottom:.2f}m\n📐 Side Profile: {record.side_profile:.2f}m\n🚪 Door Profile: {record.door_profile:.2f}m\n\n📊 TOTAL PROFILE: {record.total_profile:.2f}m'''
                return {'type': 'ir.actions.client','tag': 'display_notification','params': {'title': 'Profile Calculation Complete','message': message,'type': 'success','sticky': True,}}
            except Exception as e:
                _logger.error(f"Error in profile calculation: {e}")
                return {'type': 'ir.actions.client','tag': 'display_notification','params': {'title': 'Profile Calculation Error','message': f'Error occurred: {str(e)}','type': 'danger',}}
    
    def action_accessories_summary(self):
        sections_summary = []
        if self.profiles_component_ids:
            sections_summary.append(f"📏 Profiles: {len(self.profiles_component_ids)} items")
        if self.brackets_component_ids:
            sections_summary.append(f"🔧 Brackets: {len(self.brackets_component_ids)} items")
        if self.wires_connectors_component_ids:
            sections_summary.append(f"🔗 Wires & Connectors: {len(self.wires_connectors_component_ids)} items")
        if self.clamps_component_ids:
            sections_summary.append(f"🛠️ Clamps: {len(self.clamps_component_ids)} items")
        
        message = f'''ACCESSORIES SUMMARY:\n\nConfiguration:\n- Gutter Bracket: {dict(self._fields['gutter_bracket_type'].selection)[self.gutter_bracket_type]}\n- Zigzag Wire: {'Enabled (' + self.zigzag_wire_size + ')' if self.enable_zigzag_wire else 'Disabled'}\n- Column Bracket: {dict(self._fields['column_bracket_type'].selection)[self.column_bracket_type]}\n- Roll Up Connectors: {'Enabled' if self.enable_rollup_connectors else 'Disabled'}\n\nProfile Summary:\n📊 Total Profile: {self.total_profile:.2f}m\n\nComponents:\n{chr(10).join(sections_summary) if sections_summary else 'No accessories components'}\n\nCosts:\n📏 Profiles: {self.total_profiles_cost:.2f}\n🔧 Brackets: {self.total_brackets_cost:.2f}\n🔗 Wires & Connectors: {self.total_wires_connectors_cost:.2f}\n🛠️ Clamps: {self.total_clamps_cost:.2f}\n\n📊 TOTAL ACCESSORIES: {self.total_accessories_cost:.2f}\n💰 GRAND TOTAL: {self.grand_total_cost:.2f}'''
        return {'type': 'ir.actions.client','tag': 'display_notification','params': {'title': 'Accessories Summary','message': message,'type': 'info','sticky': True,}}
    
    def action_view_clamp_details(self):
        wizard = self.env['clamp.calculation.detail'].create({'green_master_id': self.id,})
        wizard.calculate_clamps()
        return {'type': 'ir.actions.act_window','name': 'Clamp Calculation Details','res_model': 'clamp.calculation.detail','res_id': wizard.id,'view_mode': 'form','view_id': self.env.ref('green2_accessories_2.view_clamp_calculation_detail_form').id,'target': 'new','context': self.env.context,}
    
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