# -*- coding: utf-8 -*-
from odoo import models, fields, api
from math import ceil
import logging

_logger = logging.getLogger(__name__)

class GreenMasterProfiles(models.Model):
    _inherit = 'green.master'
    
    # Profile calculation fields
    profiles_for_arch = fields.Float('Profiles For Arch', compute='_compute_all_profiles', store=True)
    profile_for_purlin = fields.Float('Profile For Purlin', compute='_compute_all_profiles', store=True)
    profile_for_bottom = fields.Float('Profile for Bottom', compute='_compute_all_profiles', store=True)
    side_profile = fields.Float('Side Profile', compute='_compute_all_profiles', store=True)
    door_profile = fields.Float('Door Profile', compute='_compute_all_profiles', store=True)
    total_profile = fields.Float('Total Profile', compute='_compute_all_profiles', store=True)
    
    @api.depends('no_of_spans', 'span_length', 'small_arch_length', 'big_arch_length',
                 'length_vent_big_arch_support', 'length_vent_small_arch_support',
                 'truss_component_ids.total_length', 'lower_component_ids.total_length',
                 'asc_component_ids.total_length', 'gutter_type', 'column_height',
                 'is_side_coridoors', 'bay_width', 'bay_length')
    def _compute_all_profiles(self):
        """Calculate all profile types"""
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
        """Calculate profiles needed for arch components"""
        try:
            if self.span_length <= 0 or self.no_of_spans <= 0:
                return 0
            
            # Get vent support lengths
            vent_big_length = 0
            vent_small_length = 0
            
            if hasattr(self, 'length_vent_big_arch_support') and self.length_vent_big_arch_support:
                vent_big_length = self.length_vent_big_arch_support.length_value
            
            if hasattr(self, 'length_vent_small_arch_support') and self.length_vent_small_arch_support:
                vent_small_length = self.length_vent_small_arch_support.length_value
            
            # Calculate roundup factor
            roundup_factor = ceil((self.span_length / 20) + 1)
            
            # Total arch length
            arch_total_length = self.small_arch_length + self.big_arch_length + vent_big_length + vent_small_length
            
            # Calculate profiles for arch
            profiles_for_arch = self.no_of_spans * roundup_factor * arch_total_length
            
            return profiles_for_arch
        except Exception as e:
            _logger.error(f"Error calculating profiles for arch: {e}")
            return 0
    
    def _calculate_profile_for_purlin(self):
        """Calculate profiles needed for purlin components"""
        try:
            total_purlin_profile = 0
            
            # Big Arch Purlin
            big_arch_purlin = self.truss_component_ids.filtered(lambda c: c.name == 'Big Arch Purlin')
            if big_arch_purlin:
                total_purlin_profile += big_arch_purlin.total_length
            
            # Small Arch Purlin
            small_arch_purlin = self.truss_component_ids.filtered(lambda c: c.name == 'Small Arch Purlin')
            if small_arch_purlin:
                total_purlin_profile += small_arch_purlin.total_length
            
            # Gutter Purlin (based on gutter type)
            if self.gutter_type == 'continuous':
                gutter_purlin = self.lower_component_ids.filtered(lambda c: c.name == 'Gutter Purlin')
                if gutter_purlin:
                    total_purlin_profile += gutter_purlin.total_length
            elif self.gutter_type == 'ippf':
                gutter_ippf = self.lower_component_ids.filtered(lambda c: c.name == 'Gutter IPPF Full')
                if gutter_ippf:
                    total_purlin_profile += gutter_ippf.total_length * 2
            
            # Gable Purlin
            gable_purlin = self.truss_component_ids.filtered(lambda c: c.name == 'Gable Purlin')
            if gable_purlin:
                total_purlin_profile += gable_purlin.total_length
            
            return total_purlin_profile
        except Exception as e:
            _logger.error(f"Error calculating profile for purlin: {e}")
            return 0
    
    def _calculate_profile_for_bottom(self):
        """Calculate profiles needed for bottom components"""
        try:
            profile_for_bottom = self.span_length * 2
            return profile_for_bottom
        except Exception as e:
            _logger.error(f"Error calculating profile for bottom: {e}")
            return 0
    
    def _calculate_side_profile(self):
        """Calculate profiles needed for side components"""
        try:
            side_profile = 0
            
            # Bay Side Border Purlin
            bay_border = self.truss_component_ids.filtered(lambda c: c.name == 'Bay Side Border Purlin')
            if bay_border:
                side_profile += bay_border.total_length
            
            # Span Side Border Purlin
            span_border = self.truss_component_ids.filtered(lambda c: c.name == 'Span Side Border Purlin')
            if span_border:
                side_profile += span_border.total_length
            
            # Calculate multiplier based on ASC configuration
            multiplier_length = 0
            
            if self.is_side_coridoors:
                # Get ASC lengths
                asc_lengths = []
                asc_names = ['Front Span ASC Pipes', 'Back Span ASC Pipes',
                            'Front Bay ASC Pipes', 'Back Bay ASC Pipes']
                
                for asc_name in asc_names:
                    asc_component = self.asc_component_ids.filtered(lambda c: asc_name in c.name)
                    if asc_component:
                        asc_lengths.append(asc_component.length)
                
                multiplier_length = max(asc_lengths) if asc_lengths else self.column_height
            else:
                multiplier_length = self.column_height
            
            # Add side profile (8 corners)
            side_profile += 8 * multiplier_length
            
            return side_profile
        except Exception as e:
            _logger.error(f"Error calculating side profile: {e}")
            return 0
    
    def _calculate_door_profile(self):
        """Calculate profiles needed for door components"""
        try:
            door_profile = 0
            
            # Regular doors
            if hasattr(self, 'door_component_ids') and self.door_component_ids:
                door_profile += sum(self.door_component_ids.mapped('total_length'))
            
            # Tractor doors
            if hasattr(self, 'tractor_door_component_ids') and self.tractor_door_component_ids:
                door_profile += sum(self.tractor_door_component_ids.mapped('total_length'))
            
            return door_profile
        except Exception as e:
            _logger.error(f"Error calculating door profile: {e}")
            return 0
    
    def _calculate_total_profile(self):
        """Calculate total profile length"""
        try:
            total = (
                self.profiles_for_arch +
                self.profile_for_purlin +
                self.profile_for_bottom +
                self.side_profile +
                self.door_profile
            )
            return total
        except Exception as e:
            _logger.error(f"Error calculating total profile: {e}")
            return 0
    
    def _calculate_all_accessories(self):
        """Extend to add profile component"""
        super()._calculate_all_accessories()
        self._create_total_profile_component()
    
    def _create_total_profile_component(self):
        """Create profile component in accessories"""
        if self.total_profile > 0:
            # Find or create master record
            master_record = self.env['accessories.master'].search([
                ('name', '=', 'Total Profile'),
                ('category', '=', 'profiles'),
                ('active', '=', True)
            ], limit=1)
            
            unit_price = master_record.unit_price if master_record else 5.00
            
            self._create_accessory_component(
                'profiles',
                'Total Profile',
                int(self.total_profile),
                'meters',
                unit_price
            )
            _logger.info(f"Created Total Profile component: {self.total_profile}m")
    
    def action_calculate_profiles(self):
        """Action to calculate profile breakdown"""
        for record in self:
            try:
                record._compute_all_profiles()
                
                message = f'''PROFILE CALCULATION BREAKDOWN:\n\n
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
