# -*- coding: utf-8 -*-
from odoo import models, fields, api
from math import ceil
import logging

_logger = logging.getLogger(__name__)

class GreenMaster(models.Model):
    _inherit = 'green.master'
    
    # Accessories Profile Fields
    profiles_for_arch = fields.Float('Profiles For Arch', compute='_compute_accessories_profiles', store=True)
    profile_for_purlin = fields.Float('Profile For Purlin', compute='_compute_accessories_profiles', store=True)
    profile_for_bottom = fields.Float('Profile for Bottom', compute='_compute_accessories_profiles', store=True)
    side_profile = fields.Float('Side Profile', compute='_compute_accessories_profiles', store=True)
    door_profile = fields.Float('Door Profile', compute='_compute_accessories_profiles', store=True)
    total_profile = fields.Float('Total Profile', compute='_compute_accessories_profiles', store=True)
    
    # Breakdown fields for report display
    arch_calculation_details = fields.Text('Arch Calculation Details', compute='_compute_accessories_profiles', store=True)
    purlin_calculation_details = fields.Text('Purlin Calculation Details', compute='_compute_accessories_profiles', store=True)
    side_calculation_details = fields.Text('Side Calculation Details', compute='_compute_accessories_profiles', store=True)
    door_calculation_details = fields.Text('Door Calculation Details', compute='_compute_accessories_profiles', store=True)

    @api.depends(
        'no_of_spans', 'span_length', 'small_arch_length', 'big_arch_length',
        'length_vent_big_arch_support', 'length_vent_small_arch_support',
        'truss_component_ids.total_length', 'lower_component_ids.total_length',
        'gutter_type', 'bay_width', 'column_height', 'is_side_coridoors',
        'door_component_ids.total_length'
    )
    def _compute_accessories_profiles(self):
        """Compute all accessories profile calculations"""
        for record in self:
            try:
                # A. Profiles For Arch
                arch_profile, arch_details = record._calculate_profiles_for_arch()
                record.profiles_for_arch = arch_profile
                record.arch_calculation_details = arch_details
                
                # B. Profile For Purlin
                purlin_profile, purlin_details = record._calculate_profile_for_purlin()
                record.profile_for_purlin = purlin_profile
                record.purlin_calculation_details = purlin_details
                
                # C. Profile for Bottom
                record.profile_for_bottom = record.span_length * 2
                
                # D. Side Profile
                side_profile, side_details = record._calculate_side_profile()
                record.side_profile = side_profile
                record.side_calculation_details = side_details
                
                # E. Door Profile
                door_profile, door_details = record._calculate_door_profile()
                record.door_profile = door_profile
                record.door_calculation_details = door_details
                
                # F. Total Profile
                record.total_profile = (record.profiles_for_arch + record.profile_for_purlin + 
                                      record.profile_for_bottom + record.side_profile + record.door_profile)
                
            except Exception as e:
                _logger.error(f"Error calculating accessories profiles: {e}")
                record.profiles_for_arch = 0
                record.profile_for_purlin = 0
                record.profile_for_bottom = 0
                record.side_profile = 0
                record.door_profile = 0
                record.total_profile = 0
                record.arch_calculation_details = f"Error: {str(e)}"
                record.purlin_calculation_details = ""
                record.side_calculation_details = ""
                record.door_calculation_details = ""

    def _calculate_profiles_for_arch(self):
        """Calculate Profiles For Arch with breakdown"""
        try:
            # Get vent support lengths
            vent_big_length = self.length_vent_big_arch_support.length_value if self.length_vent_big_arch_support else 0
            vent_small_length = self.length_vent_small_arch_support.length_value if self.length_vent_small_arch_support else 0
            
            # Calculate: No of Spans * (Roundup((Span Length / 20) + 1) * (Small Arch + Big Arch + Vent Supports))
            span_factor = ceil((self.span_length / 20) + 1)
            arch_total = self.small_arch_length + self.big_arch_length + vent_big_length + vent_small_length
            result = self.no_of_spans * span_factor * arch_total
            
            # Create breakdown details
            details = f'''Profiles For Arch Calculation:
• No of Spans: {self.no_of_spans}
• Span Length: {self.span_length}m
• Roundup((Span Length / 20) + 1): Roundup(({self.span_length} / 20) + 1) = {span_factor}
• Small Arch Length: {self.small_arch_length}m
• Big Arch Length: {self.big_arch_length}m
• Vent Big Arch Support Length: {vent_big_length}m
• Vent Small Arch Support Length: {vent_small_length}m
• Total Arch Length: {arch_total}m
• Formula: {self.no_of_spans} × {span_factor} × {arch_total} = {result}m'''
            
            return result, details
            
        except Exception as e:
            return 0, f"Error calculating profiles for arch: {str(e)}"

    def _calculate_profile_for_purlin(self):
        """Calculate Profile For Purlin with breakdown"""
        try:
            details_lines = ["Profile For Purlin Calculation:"]
            total_purlin = 0
            
            # Base: Big Arch Purlin + Small Arch Purlin
            big_arch_purlin_component = self.truss_component_ids.filtered(lambda c: c.name == 'Big Arch Purlin')
            small_arch_purlin_component = self.truss_component_ids.filtered(lambda c: c.name == 'Small Arch Purlin')
            
            big_arch_total = sum(big_arch_purlin_component.mapped('total_length'))
            small_arch_total = sum(small_arch_purlin_component.mapped('total_length'))
            
            details_lines.append(f"• Big Arch Purlin Total Length: {big_arch_total}m")
            details_lines.append(f"• Small Arch Purlin Total Length: {small_arch_total}m")
            
            base_total = big_arch_total + small_arch_total
            total_purlin += base_total
            details_lines.append(f"• Base Total: {base_total}m")
            
            # Gutter calculations
            if self.gutter_type == 'continuous':
                gutter_purlin_component = self.lower_component_ids.filtered(lambda c: c.name == 'Gutter Purlin')
                gutter_purlin_total = sum(gutter_purlin_component.mapped('total_length'))
                total_purlin += gutter_purlin_total
                details_lines.append(f"• Continuous Gutter Purlin: {gutter_purlin_total}m")
                
            elif self.gutter_type == 'ippf':
                # IPPF Gutter Total Length * 2
                gutter_ippf_component = self.lower_component_ids.filtered(lambda c: c.name == 'Gutter IPPF Full')
                gutter_total_length = sum(gutter_ippf_component.mapped('total_length'))
                ippf_contribution = gutter_total_length * 2
                total_purlin += ippf_contribution
                details_lines.append(f"• IPPF Gutter Total Length × 2: {gutter_total_length} × 2 = {ippf_contribution}m")
                
                # Gable Purlin Total Length
                gable_purlin_component = self.truss_component_ids.filtered(lambda c: c.name == 'Gable Purlin')
                gable_total = sum(gable_purlin_component.mapped('total_length'))
                total_purlin += gable_total
                details_lines.append(f"• Gable Purlin Total Length: {gable_total}m")
            
            details_lines.append(f"• TOTAL PURLIN PROFILE: {total_purlin}m")
            details = "\n".join(details_lines)
            
            return total_purlin, details
            
        except Exception as e:
            return 0, f"Error calculating profile for purlin: {str(e)}"

    def _calculate_side_profile(self):
        """Calculate Side Profile with breakdown"""
        try:
            details_lines = ["Side Profile Calculation:"]
            
            # Bay Side Border Purlin Total Length
            bay_border_component = self.truss_component_ids.filtered(lambda c: c.name == 'Bay Side Border Purlin')
            bay_border_total = sum(bay_border_component.mapped('total_length'))
            details_lines.append(f"• Bay Side Border Purlin Total: {bay_border_total}m")
            
            # Span Side Border Purlin Total Length
            span_border_component = self.truss_component_ids.filtered(lambda c: c.name == 'Span Side Border Purlin')
            span_border_total = sum(span_border_component.mapped('total_length'))
            details_lines.append(f"• Span Side Border Purlin Total: {span_border_total}m")
            
            border_total = bay_border_total + span_border_total
            
            # 8 * (ASC max length OR Main Column Length)
            if self.is_side_coridoors:
                # Get all ASC component lengths
                asc_lengths = []
                
                front_span_asc = self.asc_component_ids.filtered(lambda c: 'Front Span ASC' in c.name)
                if front_span_asc:
                    asc_lengths.append(front_span_asc[0].length)
                    
                back_span_asc = self.asc_component_ids.filtered(lambda c: 'Back Span ASC' in c.name)
                if back_span_asc:
                    asc_lengths.append(back_span_asc[0].length)
                    
                front_bay_asc = self.asc_component_ids.filtered(lambda c: 'Front Bay ASC' in c.name)
                if front_bay_asc:
                    asc_lengths.append(front_bay_asc[0].length)
                    
                back_bay_asc = self.asc_component_ids.filtered(lambda c: 'Back Bay ASC' in c.name)
                if back_bay_asc:
                    asc_lengths.append(back_bay_asc[0].length)
                
                max_asc_length = max(asc_lengths) if asc_lengths else self.column_height
                multiplier_length = max_asc_length
                details_lines.append(f"• ASC Enabled - Max ASC Length: {max_asc_length}m")
                
            else:
                multiplier_length = self.column_height
                details_lines.append(f"• ASC Disabled - Main Column Length: {self.column_height}m")
            
            multiplier_total = 8 * multiplier_length
            details_lines.append(f"• 8 × {multiplier_length}m = {multiplier_total}m")
            
            total_side = border_total + multiplier_total
            details_lines.append(f"• TOTAL SIDE PROFILE: {border_total} + {multiplier_total} = {total_side}m")
            
            details = "\n".join(details_lines)
            return total_side, details
            
        except Exception as e:
            return 0, f"Error calculating side profile: {str(e)}"

    def _calculate_door_profile(self):
        """Calculate Door Profile from door components"""
        try:
            if not hasattr(self, 'door_component_ids') or not self.door_component_ids:
                return 0, "Door Profile: No door components found"
            
            total_door_length = sum(self.door_component_ids.mapped('total_length'))
            
            details_lines = ["Door Profile Calculation:"]
            for component in self.door_component_ids:
                details_lines.append(f"• {component.name}: {component.nos} × {component.length}m = {component.total_length}m")
            details_lines.append(f"• TOTAL DOOR PROFILE: {total_door_length}m")
            
            details = "\n".join(details_lines)
            return total_door_length, details
            
        except Exception as e:
            return 0, f"Error calculating door profile: {str(e)}"

    def action_calculate_accessories(self):
        """Manual accessories calculation button action"""
        for record in self:
            try:
                # Trigger recalculation
                record._compute_accessories_profiles()
                
                # Prepare summary message
                message = f'''ACCESSORIES PROFILE CALCULATION COMPLETED:

🏗️ Profiles For Arch: {record.profiles_for_arch:.2f}m
📏 Profile For Purlin: {record.profile_for_purlin:.2f}m  
⬇️ Profile for Bottom: {record.profile_for_bottom:.2f}m
📐 Side Profile: {record.side_profile:.2f}m
🚪 Door Profile: {record.door_profile:.2f}m

📊 TOTAL PROFILE: {record.total_profile:.2f}m

Click "Print PDF Report" to see detailed breakdown.'''
                
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

    def action_accessories_summary(self):
        """Show accessories calculation summary"""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Accessories Profile Summary',
                'message': f'''Current Accessories Profile Totals:

🏗️ Profiles For Arch: {self.profiles_for_arch:.2f}m
📏 Profile For Purlin: {self.profile_for_purlin:.2f}m  
⬇️ Profile for Bottom: {self.profile_for_bottom:.2f}m
📐 Side Profile: {self.side_profile:.2f}m
🚪 Door Profile: {self.door_profile:.2f}m

📊 TOTAL PROFILE: {self.total_profile:.2f}m''',
                'type': 'info',
                'sticky': True,
            }
        }
