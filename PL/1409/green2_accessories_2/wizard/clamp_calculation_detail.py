# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
import xlsxwriter
import io
import base64
from math import ceil

_logger = logging.getLogger(__name__)

class ClampCalculationDetail(models.TransientModel):
    _name = 'clamp.calculation.detail'
    _description = 'Clamp Calculation Detail Wizard'
    
    # Main fields
    green_master_id = fields.Many2one('green.master', string='Project', required=True)
    calculation_date = fields.Datetime('Calculation Date', default=fields.Datetime.now)
    # Add this after green_master_id field
    green_master_display = fields.Char(
        string='Project', 
        compute='_compute_green_master_display',
        store=False
    )

    # Add this compute method
    @api.depends('green_master_id', 'green_master_id.customer')
    def _compute_green_master_display(self):
        for record in self:
            if record.green_master_id and record.green_master_id.customer:
                record.green_master_display = record.green_master_id.customer
            else:
                record.green_master_display = 'No Customer Selected'
    # Calculation lines
    calculation_line_ids = fields.One2many(
        'clamp.calculation.detail.line', 
        'wizard_id', 
        string='Calculation Details'
    )
    
    # Summary fields
    total_quantity = fields.Integer('Total Clamp Quantity', compute='_compute_totals')
    total_cost = fields.Float('Total Clamp Cost', compute='_compute_totals')
    
    @api.depends('calculation_line_ids.quantity', 'calculation_line_ids.total_cost')
    def _compute_totals(self):
        for record in self:
            record.total_quantity = sum(record.calculation_line_ids.mapped('quantity'))
            record.total_cost = sum(record.calculation_line_ids.mapped('total_cost'))
    
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self._context.get('active_id') and self._context.get('active_model') == 'green.master':
            res['green_master_id'] = self._context.get('active_id')
        return res
    
    def calculate_clamps(self):
        """Main method to calculate all clamp details"""
        self.calculation_line_ids.unlink()
        
        lines_data = []
        sequence = 10
        
        project = self.green_master_id
        
        # Validate required pipe sizes
        validation_errors = self._validate_pipe_configurations()
        if validation_errors:
            raise ValidationError(_("Pipe configuration errors:\n%s") % "\n".join(validation_errors))
        
        # Calculate based on clamp type
        if project.clamp_type == 'm_type':
            lines_data.extend(self._calculate_m_type_clamps(sequence))
            sequence += 100
            
        elif project.clamp_type == 'w_type':
            lines_data.extend(self._calculate_w_type_clamps(sequence))
            sequence += 100
        
        # Calculate V Support to Main Column Clamps
        lines_data.extend(self._calculate_v_support_main_column_clamps(sequence))
        sequence += 100
        
        # Calculate Cross Bracing Clamps
        lines_data.extend(self._calculate_cross_bracing_clamps(sequence))
        sequence += 100
        
        # Calculate ASC Support Clamps
        if project.is_side_coridoors and project.support_hockeys > 0:
            lines_data.extend(self._calculate_asc_support_clamps(sequence))
            sequence += 100
        
        # Calculate ASC Bracket Clamps (Gutter Arch Brackets)
        if project.gutter_bracket_type == 'arch':
            lines_data.extend(self._calculate_asc_bracket_clamps(sequence))
            sequence += 100
        
        # Calculate Border Purlin Clamps
        if int(project.bay_side_border_purlin) > 0 or int(project.span_side_border_purlin) > 0:
            lines_data.extend(self._calculate_border_purlin_clamps(sequence))
            sequence += 100
        
        # NEW: Calculate Arch Middle Purlin Clamps
        lines_data.extend(self._calculate_arch_middle_purlin_clamps(sequence))
        
        # Create all lines
        for line_data in lines_data:
            self.env['clamp.calculation.detail.line'].create(line_data)
        
        return True
    
    def _validate_pipe_configurations(self):
        """Validate that required pipe sizes are configured"""
        errors = []
        project = self.green_master_id
        
        # Check for arch middle purlin configurations
        if project.arch_middle_purlin_big_arch != '0':
            big_arch = project.truss_component_ids.filtered(lambda c: c.name == 'Big Arch')
            if not big_arch or not big_arch.pipe_id:
                errors.append("Big Arch pipe not configured but required for Arch Middle Purlin Big Arch clamps")
        
        if project.arch_middle_purlin_small_arch != '0':
            small_arch = project.truss_component_ids.filtered(lambda c: c.name == 'Small Arch')
            if not small_arch or not small_arch.pipe_id:
                errors.append("Small Arch pipe not configured but required for Arch Middle Purlin Small Arch clamps")
        
        # Check for W/M type configurations
        if project.clamp_type in ['w_type', 'm_type']:
            bottom_chord = project.truss_component_ids.filtered(
                lambda c: 'Bottom Chord' in c.name and 'V Support' not in c.name
            )
            if bottom_chord and not any(c.pipe_id for c in bottom_chord):
                errors.append(f"{project.clamp_type.upper()} clamps require Bottom Chord pipe configuration")
        
        return errors
    
    def _calculate_m_type_clamps(self, sequence):
        """Calculate M Type clamp details"""
        lines = []
        project = self.green_master_id
        
        # Bottom Chord calculations
        bottom_chord_data = project._get_bottom_chord_data()
        bottom_chord_data['count'] = ceil(bottom_chord_data['count'] - (bottom_chord_data.get('afs_count', 0)/2))
        v_support = project._get_v_support_count()
        
        if bottom_chord_data['count'] > 0 and bottom_chord_data['size']:
            multiplier = 3 if project.bottom_chord_clamp_type == 'single' else 5
            qty = (bottom_chord_data['count'] * multiplier) + v_support
            
            lines.append({
                'wizard_id': self.id,
                'sequence': sequence,
                'category': 'M TYPE CLAMPS',
                'component': f"Bottom Chord ({project.bottom_chord_clamp_type.title()})",
                'clamp_type': 'Full Clamp',
                'size': bottom_chord_data['size'],
                'quantity': int(qty),
                'formula': f"({bottom_chord_data['count']} × {multiplier}) + {v_support}",
                'unit_price': self._get_clamp_unit_price('Full Clamp', bottom_chord_data['size']),
            })
            sequence += 10
        
        # Add other M type calculations...
        lines.extend(self._calculate_common_arch_clamps('M TYPE CLAMPS', sequence))
        
        return lines
    
    def _calculate_w_type_clamps(self, sequence):
        """Calculate W Type clamp details"""
        lines = []
        project = self.green_master_id
        
        # Bottom Chord calculations (similar to M type)
        bottom_chord_data = project._get_bottom_chord_data()
        bottom_chord_data['count'] = ceil(bottom_chord_data['count'] - (bottom_chord_data.get('afs_count', 0)/2))
        v_support = project._get_v_support_count()
        
        if bottom_chord_data['count'] > 0 and bottom_chord_data['size']:
            qty = (bottom_chord_data['count'] * 3) + v_support
            lines.append({
                'wizard_id': self.id,
                'sequence': sequence,
                'category': 'W TYPE CLAMPS',
                'component': 'Bottom Chord',
                'clamp_type': 'Full Clamp',
                'size': bottom_chord_data['size'],
                'quantity': int(qty),
                'formula': f"({bottom_chord_data['count']} × 3) + {v_support}",
                'unit_price': self._get_clamp_unit_price('Full Clamp', bottom_chord_data['size']),
            })
            sequence += 10
        
        # Purlin clamps
        lines.extend(self._calculate_w_type_purlin_clamps(sequence))
        sequence += 50
        
        # Common arch clamps
        lines.extend(self._calculate_common_arch_clamps('W TYPE CLAMPS', sequence))
        
        return lines
    
    def _calculate_w_type_purlin_clamps(self, start_sequence):
        """Calculate W Type purlin clamps"""
        lines = []
        project = self.green_master_id
        sequence = start_sequence
        
        big_arch_data = project._get_big_arch_data()
        small_arch_data = project._get_small_arch_data()
        
        # Big Purlin Clamps
        if big_arch_data['size'] and project.big_purlin_clamp_type_first:
            qty_first = project.no_of_spans * 2
            clamp_name = 'Full Clamp' if project.big_purlin_clamp_type_first == 'full_clamp' else 'L Joint'
            
            lines.append({
                'wizard_id': self.id,
                'sequence': sequence,
                'category': 'W TYPE CLAMPS',
                'component': 'Big Purlin (First Type)',
                'clamp_type': clamp_name,
                'size': big_arch_data['size'],
                'quantity': int(qty_first),
                'formula': f"No of Spans × 2 = {project.no_of_spans} × 2",
                'unit_price': self._get_clamp_unit_price(clamp_name, big_arch_data['size']),
            })
            sequence += 10
            
            if project.big_purlin_clamp_type_second:
                qty_second = big_arch_data['count'] - qty_first
                if qty_second > 0:
                    clamp_name = 'Half Clamp' if project.big_purlin_clamp_type_second == 'half_clamp' else 'T Joint'
                    lines.append({
                        'wizard_id': self.id,
                        'sequence': sequence,
                        'category': 'W TYPE CLAMPS',
                        'component': 'Big Purlin (Second Type)',
                        'clamp_type': clamp_name,
                        'size': big_arch_data['size'],
                        'quantity': int(qty_second),
                        'formula': f"Remaining = {big_arch_data['count']} - {qty_first}",
                        'unit_price': self._get_clamp_unit_price(clamp_name, big_arch_data['size']),
                    })
                    sequence += 10
        
        # Small Purlin Clamps (similar logic)
        if small_arch_data['size'] and project.small_purlin_clamp_type_first:
            qty_first = project.no_of_spans * 2
            clamp_name = 'Full Clamp' if project.small_purlin_clamp_type_first == 'full_clamp' else 'L Joint'
            
            lines.append({
                'wizard_id': self.id,
                'sequence': sequence,
                'category': 'W TYPE CLAMPS',
                'component': 'Small Purlin (First Type)',
                'clamp_type': clamp_name,
                'size': small_arch_data['size'],
                'quantity': int(qty_first),
                'formula': f"No of Spans × 2 = {project.no_of_spans} × 2",
                'unit_price': self._get_clamp_unit_price(clamp_name, small_arch_data['size']),
            })
            sequence += 10
            
            if project.small_purlin_clamp_type_second:
                qty_second = small_arch_data['count'] - qty_first
                if qty_second > 0:
                    clamp_name = 'Half Clamp' if project.small_purlin_clamp_type_second == 'half_clamp' else 'T Joint'
                    lines.append({
                        'wizard_id': self.id,
                        'sequence': sequence,
                        'category': 'W TYPE CLAMPS',
                        'component': 'Small Purlin (Second Type)',
                        'clamp_type': clamp_name,
                        'size': small_arch_data['size'],
                        'quantity': int(qty_second),
                        'formula': f"Remaining = {small_arch_data['count']} - {qty_first}",
                        'unit_price': self._get_clamp_unit_price(clamp_name, small_arch_data['size']),
                    })
                    sequence += 10
        
        return lines
    
    def _calculate_common_arch_clamps(self, category, start_sequence):
        """Calculate common arch clamps for both W and M types"""
        lines = []
        project = self.green_master_id
        sequence = start_sequence
        
        big_arch_data = project._get_big_arch_data()
        small_arch_data = project._get_small_arch_data()
        vent_support = project._get_vent_support_big_arch_count()
        
        # Big Arch Full Clamps
        if big_arch_data['count'] > 0 and big_arch_data['size']:
            qty = (big_arch_data['count'] * 2) + vent_support
            lines.append({
                'wizard_id': self.id,
                'sequence': sequence,
                'category': category,
                'component': 'Big Arch',
                'clamp_type': 'Full Clamp',
                'size': big_arch_data['size'],
                'quantity': int(qty),
                'formula': f"({big_arch_data['count']} × 2) + {vent_support}" if vent_support > 0 else f"{big_arch_data['count']} × 2",
                'unit_price': self._get_clamp_unit_price('Full Clamp', big_arch_data['size']),
            })
            sequence += 10
        
        # Small Arch Full Clamps
        if small_arch_data['count'] > 0 and small_arch_data['size']:
            lines.append({
                'wizard_id': self.id,
                'sequence': sequence,
                'category': category,
                'component': 'Small Arch',
                'clamp_type': 'Full Clamp',
                'size': small_arch_data['size'],
                'quantity': int(small_arch_data['count']),
                'formula': f"Total Small Arches = {small_arch_data['count']}",
                'unit_price': self._get_clamp_unit_price('Full Clamp', small_arch_data['size']),
            })
            sequence += 10
        
        # Arch Support Straight Middle (W Type specific)
        if category == 'W TYPE CLAMPS':
            arch_support_data = project._get_arch_support_straight_middle_data()
            if arch_support_data['count'] > 0 and arch_support_data['size']:
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': category,
                    'component': 'Arch Support Straight',
                    'clamp_type': 'Full Clamp',
                    'size': arch_support_data['size'],
                    'quantity': int(arch_support_data['count']),
                    'formula': f"Total = {arch_support_data['count']}",
                    'unit_price': self._get_clamp_unit_price('Full Clamp', arch_support_data['size']),
                })
                sequence += 10
                
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': category,
                    'component': 'Arch Support Straight',
                    'clamp_type': 'Half Clamp',
                    'size': arch_support_data['size'],
                    'quantity': int(arch_support_data['count']),
                    'formula': f"Total = {arch_support_data['count']}",
                    'unit_price': self._get_clamp_unit_price('Half Clamp', arch_support_data['size']),
                })
        
        return lines
    
    def _calculate_v_support_main_column_clamps(self, sequence):
        """Calculate V Support to Main Column Clamps"""
        lines = []
        project = self.green_master_id
        
        v_support_count = project._get_v_support_count()
        main_column_size = project._get_main_column_pipe_size()
        
        if v_support_count > 0 and main_column_size:
            # Half clamps calculation
            anchor_frame_count = project.no_anchor_frame_lines * project.no_of_spans
            half_qty = (v_support_count / 2) - (2 * (anchor_frame_count - 2))
            
            if half_qty > 0:
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'V SUPPORT TO MAIN COLUMN CLAMPS',
                    'component': 'Half Clamps',
                    'clamp_type': 'Half Clamp',
                    'size': main_column_size,
                    'quantity': int(half_qty),
                    'formula': f"({v_support_count} / 2) - (2 × ({anchor_frame_count} - 2))",
                    'unit_price': self._get_clamp_unit_price('Half Clamp', main_column_size),
                })
                sequence += 10
            
            # Full clamps
            lines.append({
                'wizard_id': self.id,
                'sequence': sequence,
                'category': 'V SUPPORT TO MAIN COLUMN CLAMPS',
                'component': 'Full Clamps',
                'clamp_type': 'Full Clamp',
                'size': main_column_size,
                'quantity': int(half_qty) if half_qty > 0 else 0,
                'formula': f"Same as half clamps",
                'unit_price': self._get_clamp_unit_price('Full Clamp', main_column_size),
            })
        
        return lines
    
    def _calculate_cross_bracing_clamps(self, sequence):
        """Calculate Cross Bracing Clamps"""
        lines = []
        project = self.green_master_id
        
        # Front/Back CC Cross Bracing
        if project.front_back_c_c_cross_bracing_x:
            no_clamps = (project.no_of_spans + 1) * 4
            main_column_size = project._get_main_column_pipe_size()
            
            if main_column_size:
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'FRONT/BACK CC CROSS BRACING',
                    'component': 'Main Column Clamps',
                    'clamp_type': 'Full Clamp',
                    'size': main_column_size,
                    'quantity': int(no_clamps),
                    'formula': f"({project.no_of_spans + 1}) × 4",
                    'unit_price': self._get_clamp_unit_price('Full Clamp', main_column_size),
                })
                sequence += 10
        
        # Column to Arch Bracing
        if project.cross_bracing_column_arch:
            big_arch_size = project._get_big_arch_data()['size']
            small_arch_size = project._get_small_arch_data()['size']
            main_column_size = project._get_main_column_pipe_size()
            
            total_bracing = project.no_of_spans * 4
            
            if big_arch_size:
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'COLUMN TO ARCH BRACING',
                    'component': 'Big Arch Clamps',
                    'clamp_type': 'Full Clamp',
                    'size': big_arch_size,
                    'quantity': int(total_bracing / 2),
                    'formula': f"{total_bracing} / 2 (half of total)",
                    'unit_price': self._get_clamp_unit_price('Full Clamp', big_arch_size),
                })
                sequence += 10
            
            if small_arch_size:
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'COLUMN TO ARCH BRACING',
                    'component': 'Small Arch Clamps',
                    'clamp_type': 'Full Clamp',
                    'size': small_arch_size,
                    'quantity': int(total_bracing / 2),
                    'formula': f"{total_bracing} / 2 (half of total)",
                    'unit_price': self._get_clamp_unit_price('Full Clamp', small_arch_size),
                })
                sequence += 10
            
            if main_column_size:
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'COLUMN TO ARCH BRACING',
                    'component': 'Main Column Clamps',
                    'clamp_type': 'Full Clamp',
                    'size': main_column_size,
                    'quantity': int(total_bracing),
                    'formula': f"Total = {total_bracing}",
                    'unit_price': self._get_clamp_unit_price('Full Clamp', main_column_size),
                })
                sequence += 10
        
        # Column to Bottom Bracing
        if project.cross_bracing_column_bottom:
            bottom_chord_size = project._get_bottom_chord_data()['size']
            main_column_size = project._get_main_column_pipe_size()
            
            total_bracing = project.no_of_spans * 4
            
            if bottom_chord_size:
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'COLUMN TO BOTTOM BRACING',
                    'component': 'Bottom Chord Clamps',
                    'clamp_type': 'Full Clamp',
                    'size': bottom_chord_size,
                    'quantity': int(total_bracing),
                    'formula': f"Total = {total_bracing}",
                    'unit_price': self._get_clamp_unit_price('Full Clamp', bottom_chord_size),
                })
                sequence += 10
            
            if main_column_size:
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'COLUMN TO BOTTOM BRACING',
                    'component': 'Main Column Clamps',
                    'clamp_type': 'Full Clamp',
                    'size': main_column_size,
                    'quantity': int(total_bracing),
                    'formula': f"Total = {total_bracing}",
                    'unit_price': self._get_clamp_unit_price('Full Clamp', main_column_size),
                })
        
        return lines
    
    def _calculate_asc_support_clamps(self, sequence):
        """Calculate ASC Support Clamps"""
        lines = []
        project = self.green_master_id
        
        # Type A: Direct ASC Pipe Clamps
        asc_support_count = project._get_asc_support_pipes_count()
        asc_pipe_size = project._get_asc_pipe_size()
        
        if asc_support_count > 0 and asc_pipe_size:
            lines.append({
                'wizard_id': self.id,
                'sequence': sequence,
                'category': 'ASC SUPPORT CLAMPS',
                'component': 'Type A - ASC Pipes',
                'clamp_type': 'Full Clamp',
                'size': asc_pipe_size,
                'quantity': int(asc_support_count),
                'formula': f"Total ASC Support = {asc_support_count}",
                'unit_price': self._get_clamp_unit_price('Full Clamp', asc_pipe_size),
            })
            sequence += 10
        
        # Type B: Column-based clamps
        column_clamps = project._calculate_asc_column_clamps()
        
        if column_clamps['thick_count'] > 0:
            thick_size = project._get_thick_column_pipe_size()
            if thick_size:
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'ASC SUPPORT CLAMPS',
                    'component': 'Type B - Thick Columns',
                    'clamp_type': 'Full Clamp',
                    'size': thick_size,
                    'quantity': int(column_clamps['thick_count']),
                    'formula': f"Thick columns × Support/Hockey",
                    'unit_price': self._get_clamp_unit_price('Full Clamp', thick_size),
                })
                sequence += 10
        
        if column_clamps['middle_count'] > 0:
            middle_size = project._get_middle_column_pipe_size()
            if middle_size:
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'ASC SUPPORT CLAMPS',
                    'component': 'Type B - Middle Columns',
                    'clamp_type': 'Full Clamp',
                    'size': middle_size,
                    'quantity': int(column_clamps['middle_count']),
                    'formula': f"Middle columns × Support/Hockey",
                    'unit_price': self._get_clamp_unit_price('Full Clamp', middle_size),
                })
                sequence += 10
        
        if column_clamps['main_count'] > 0:
            main_size = project._get_main_column_pipe_size()
            if main_size:
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'ASC SUPPORT CLAMPS',
                    'component': 'Type B - Main Columns',
                    'clamp_type': 'Full Clamp',
                    'size': main_size,
                    'quantity': int(column_clamps['main_count']),
                    'formula': f"Remaining ASC Support",
                    'unit_price': self._get_clamp_unit_price('Full Clamp', main_size),
                })
        
        return lines
    
    def _calculate_asc_bracket_clamps(self, sequence):
        """Calculate ASC Bracket (Gutter Arch Bracket) Clamps"""
        lines = []
        project = self.green_master_id
        
        # Check if Bay Side clamps required
        has_bay_asc = project.width_front_bay_coridoor > 0 or project.width_back_bay_coridoor > 0
        
        if has_bay_asc:
            lines.append({
                'wizard_id': self.id,
                'sequence': sequence,
                'category': 'ASC BRACKET CLAMPS',
                'component': 'Gutter Arch Brackets',
                'clamp_type': 'Info',
                'size': 'N/A',
                'quantity': 0,
                'formula': 'Bay Side Clamp Required: Yes',
                'unit_price': 0,
            })
        else:
            lines.append({
                'wizard_id': self.id,
                'sequence': sequence,
                'category': 'ASC BRACKET CLAMPS',
                'component': 'Gutter Arch Brackets',
                'clamp_type': 'Info',
                'size': 'N/A',
                'quantity': 0,
                'formula': 'Bay Side Clamp Required: No\nCalculating only for Span ASC',
                'unit_price': 0,
            })
        
        return lines
    
    def _calculate_border_purlin_clamps(self, sequence):
        """Calculate Border Purlin Clamps"""
        lines = []
        project = self.green_master_id
        
        # Bay Side Border Clamps
        if int(project.bay_side_border_purlin) > 0:
            lines.extend(self._calculate_bay_side_border_clamps(sequence))
            sequence += 50
        
        # Span Side Border Clamps
        if int(project.span_side_border_purlin) > 0:
            lines.extend(self._calculate_span_side_border_clamps(sequence))
            sequence += 50
        
        # Anchor Frame Lines
        if project.no_anchor_frame_lines >= 1:
            lines.extend(self._calculate_anchor_frame_clamps(sequence))
        
        return lines
    
    def _calculate_bay_side_border_clamps(self, sequence):
        """Calculate Bay Side Border Purlin Clamps"""
        lines = []
        project = self.green_master_id
        bay_side_value = int(project.bay_side_border_purlin)
        
        # Front Bay
        if project.width_front_bay_coridoor > 0:
            pipe_size = project._get_asc_pipe_size()
            hockey_count = project._get_front_bay_hockey_count()
            
            if pipe_size and hockey_count > 0:
                # Half Clamps
                half_qty = (hockey_count - 1) * bay_side_value
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'BORDER PURLIN - BAY SIDE',
                    'component': 'Front Bay (ASC)',
                    'clamp_type': 'Half Clamp',
                    'size': pipe_size,
                    'quantity': int(half_qty),
                    'formula': f"({hockey_count - 1}) × {bay_side_value}",
                    'unit_price': self._get_clamp_unit_price('Half Clamp', pipe_size),
                })
                sequence += 10
                
                # Full Clamps
                full_qty = 2 * bay_side_value
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'BORDER PURLIN - BAY SIDE',
                    'component': 'Front Bay (ASC)',
                    'clamp_type': 'Full Clamp',
                    'size': pipe_size,
                    'quantity': int(full_qty),
                    'formula': f"2 × {bay_side_value}",
                    'unit_price': self._get_clamp_unit_price('Full Clamp', pipe_size),
                })
                sequence += 10
        else:
            half_size, full_size = project._get_bay_side_pipe_sizes('front')
            if half_size and full_size:
                # Half Clamps
                half_qty = project.no_of_bays * bay_side_value
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'BORDER PURLIN - BAY SIDE',
                    'component': f'Front Bay (Thick Config: {project.thick_column})',
                    'clamp_type': 'Half Clamp',
                    'size': half_size,
                    'quantity': int(half_qty),
                    'formula': f"{project.no_of_bays} × {bay_side_value}",
                    'unit_price': self._get_clamp_unit_price('Half Clamp', half_size),
                })
                sequence += 10
                
                # Full Clamps
                full_qty = 2 * bay_side_value
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'BORDER PURLIN - BAY SIDE',
                    'component': f'Front Bay (Thick Config: {project.thick_column})',
                    'clamp_type': 'Full Clamp',
                    'size': full_size,
                    'quantity': int(full_qty),
                    'formula': f"2 × {bay_side_value}",
                    'unit_price': self._get_clamp_unit_price('Full Clamp', full_size),
                })
                sequence += 10
        
        # Back Bay (similar logic)
        if project.width_back_bay_coridoor > 0:
            pipe_size = project._get_asc_pipe_size()
            hockey_count = project._get_back_bay_hockey_count()
            
            if pipe_size and hockey_count > 0:
                half_qty = (hockey_count - 1) * bay_side_value
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'BORDER PURLIN - BAY SIDE',
                    'component': 'Back Bay (ASC)',
                    'clamp_type': 'Half Clamp',
                    'size': pipe_size,
                    'quantity': int(half_qty),
                    'formula': f"({hockey_count - 1}) × {bay_side_value}",
                    'unit_price': self._get_clamp_unit_price('Half Clamp', pipe_size),
                })
                sequence += 10
                
                full_qty = 2 * bay_side_value
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'BORDER PURLIN - BAY SIDE',
                    'component': 'Back Bay (ASC)',
                    'clamp_type': 'Full Clamp',
                    'size': pipe_size,
                    'quantity': int(full_qty),
                    'formula': f"2 × {bay_side_value}",
                    'unit_price': self._get_clamp_unit_price('Full Clamp', pipe_size),
                })
                sequence += 10
        else:
            half_size, full_size = project._get_bay_side_pipe_sizes('back')
            if half_size and full_size:
                half_qty = project.no_of_bays * bay_side_value
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'BORDER PURLIN - BAY SIDE',
                    'component': f'Back Bay (Thick Config: {project.thick_column})',
                    'clamp_type': 'Half Clamp',
                    'size': half_size,
                    'quantity': int(half_qty),
                    'formula': f"{project.no_of_bays} × {bay_side_value}",
                    'unit_price': self._get_clamp_unit_price('Half Clamp', half_size),
                })
                sequence += 10
                
                full_qty = 2 * bay_side_value
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'BORDER PURLIN - BAY SIDE',
                    'component': f'Back Bay (Thick Config: {project.thick_column})',
                    'clamp_type': 'Full Clamp',
                    'size': full_size,
                    'quantity': int(full_qty),
                    'formula': f"2 × {bay_side_value}",
                    'unit_price': self._get_clamp_unit_price('Full Clamp', full_size),
                })
        
        return lines
    
    def _calculate_span_side_border_clamps(self, sequence):
        """Calculate Span Side Border Purlin Clamps"""
        lines = []
        project = self.green_master_id
        span_side_value = int(project.span_side_border_purlin)
        big_frame_multiplier = int(project.no_column_big_frame) + 1
        
        # Front Span
        if project.width_front_span_coridoor > 0:
            pipe_size = project._get_asc_pipe_size()
            hockey_count = project._get_front_span_hockey_count()
            
            if pipe_size and hockey_count > 0:
                half_qty = (hockey_count - 1) * span_side_value
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'BORDER PURLIN - SPAN SIDE',
                    'component': 'Front Span (ASC)',
                    'clamp_type': 'Half Clamp',
                    'size': pipe_size,
                    'quantity': int(half_qty),
                    'formula': f"({hockey_count - 1}) × {span_side_value}",
                    'unit_price': self._get_clamp_unit_price('Half Clamp', pipe_size),
                })
                sequence += 10
                
                full_qty = 2 * span_side_value
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'BORDER PURLIN - SPAN SIDE',
                    'component': 'Front Span (ASC)',
                    'clamp_type': 'Full Clamp',
                    'size': pipe_size,
                    'quantity': int(full_qty),
                    'formula': f"2 × {span_side_value}",
                    'unit_price': self._get_clamp_unit_price('Full Clamp', pipe_size),
                })
                sequence += 10
        else:
            half_size, full_size = project._get_span_side_pipe_sizes('front')
            if half_size and full_size:
                half_qty = (project.no_of_spans * big_frame_multiplier) * span_side_value
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'BORDER PURLIN - SPAN SIDE',
                    'component': f'Front Span (Thick Config: {project.thick_column})',
                    'clamp_type': 'Half Clamp',
                    'size': half_size,
                    'quantity': int(half_qty),
                    'formula': f"({project.no_of_spans} × {big_frame_multiplier}) × {span_side_value}",
                    'unit_price': self._get_clamp_unit_price('Half Clamp', half_size),
                })
                sequence += 10
                
                full_qty = 2 * span_side_value
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'BORDER PURLIN - SPAN SIDE',
                    'component': f'Front Span (Thick Config: {project.thick_column})',
                    'clamp_type': 'Full Clamp',
                    'size': full_size,
                    'quantity': int(full_qty),
                    'formula': f"2 × {span_side_value}",
                    'unit_price': self._get_clamp_unit_price('Full Clamp', full_size),
                })
                sequence += 10
        
        # Back Span (similar logic)
        if project.width_back_span_coridoor > 0:
            pipe_size = project._get_asc_pipe_size()
            hockey_count = project._get_back_span_hockey_count()
            
            if pipe_size and hockey_count > 0:
                half_qty = (hockey_count - 1) * span_side_value
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'BORDER PURLIN - SPAN SIDE',
                    'component': 'Back Span (ASC)',
                    'clamp_type': 'Half Clamp',
                    'size': pipe_size,
                    'quantity': int(half_qty),
                    'formula': f"({hockey_count - 1}) × {span_side_value}",
                    'unit_price': self._get_clamp_unit_price('Half Clamp', pipe_size),
                })
                sequence += 10
                
                full_qty = 2 * span_side_value
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'BORDER PURLIN - SPAN SIDE',
                    'component': 'Back Span (ASC)',
                    'clamp_type': 'Full Clamp',
                    'size': pipe_size,
                    'quantity': int(full_qty),
                    'formula': f"2 × {span_side_value}",
                    'unit_price': self._get_clamp_unit_price('Full Clamp', pipe_size),
                })
        else:
            half_size, full_size = project._get_span_side_pipe_sizes('back')
            if half_size and full_size:
                half_qty = (project.no_of_spans * big_frame_multiplier) * span_side_value
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'BORDER PURLIN - SPAN SIDE',
                    'component': f'Back Span (Thick Config: {project.thick_column})',
                    'clamp_type': 'Half Clamp',
                    'size': half_size,
                    'quantity': int(half_qty),
                    'formula': f"({project.no_of_spans} × {big_frame_multiplier}) × {span_side_value}",
                    'unit_price': self._get_clamp_unit_price('Half Clamp', half_size),
                })
                sequence += 10
                
                full_qty = 2 * span_side_value
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'BORDER PURLIN - SPAN SIDE',
                    'component': f'Back Span (Thick Config: {project.thick_column})',
                    'clamp_type': 'Full Clamp',
                    'size': full_size,
                    'quantity': int(full_qty),
                    'formula': f"2 × {span_side_value}",
                    'unit_price': self._get_clamp_unit_price('Full Clamp', full_size),
                })
        
        return lines
    
    def _calculate_anchor_frame_clamps(self, sequence):
        """Calculate Anchor Frame Line Clamps"""
        lines = []
        project = self.green_master_id
        span_side_value = int(project.span_side_border_purlin)
        
        if span_side_value <= 0 or project.no_anchor_frame_lines <= 0:
            return lines
        
        if project.no_anchor_frame_lines == 1:
            lines.append({
                'wizard_id': self.id,
                'sequence': sequence,
                'category': 'ANCHOR FRAME LINES',
                'component': 'Note',
                'clamp_type': 'Info',
                'size': 'N/A',
                'quantity': 0,
                'formula': 'ASC and Anchor Frame Lines considered at same line',
                'unit_price': 0,
            })
            sequence += 10
            
            # Determine pipe size
            has_asc = project.width_front_span_coridoor > 0 or project.width_back_span_coridoor > 0
            pipe_size = project._get_asc_pipe_size() if has_asc else project._get_big_column_pipe_size()
            
            if pipe_size:
                half_qty = project.no_of_spans * span_side_value
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'ANCHOR FRAME LINES',
                    'component': 'Single Anchor Frame Line',
                    'clamp_type': 'Half Clamp',
                    'size': pipe_size,
                    'quantity': int(half_qty),
                    'formula': f"{project.no_of_spans} × {span_side_value}",
                    'unit_price': self._get_clamp_unit_price('Half Clamp', pipe_size),
                })
        
        elif project.no_anchor_frame_lines >= 2:
            # Front Span Anchor Frame
            if project.width_front_span_coridoor > 0:
                pipe_size = project._get_asc_pipe_size()
            else:
                pipe_size = project._get_big_column_pipe_size()
            
            if pipe_size:
                half_qty = project.no_of_spans * span_side_value
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'ANCHOR FRAME LINES',
                    'component': 'Front Span Anchor Frame',
                    'clamp_type': 'Half Clamp',
                    'size': pipe_size,
                    'quantity': int(half_qty),
                    'formula': f"{project.no_of_spans} × {span_side_value}",
                    'unit_price': self._get_clamp_unit_price('Half Clamp', pipe_size),
                })
                sequence += 10
            
            # Back Span Anchor Frame
            if project.width_back_span_coridoor > 0:
                pipe_size = project._get_asc_pipe_size()
            else:
                pipe_size = project._get_big_column_pipe_size()
            
            if pipe_size:
                half_qty = project.no_of_spans * span_side_value
                lines.append({
                    'wizard_id': self.id,
                    'sequence': sequence,
                    'category': 'ANCHOR FRAME LINES',
                    'component': 'Back Span Anchor Frame',
                    'clamp_type': 'Half Clamp',
                    'size': pipe_size,
                    'quantity': int(half_qty),
                    'formula': f"{project.no_of_spans} × {span_side_value}",
                    'unit_price': self._get_clamp_unit_price('Half Clamp', pipe_size),
                })
        
        return lines
    
    def _calculate_arch_middle_purlin_clamps(self, sequence):
        """Calculate Arch Middle Purlin Clamps - NEW METHOD"""
        lines = []
        project = self.green_master_id
        
        # Calculate Big Arch Middle Purlin Clamps
        if project.arch_middle_purlin_big_arch != '0' and int(project.arch_middle_purlin_big_arch_pcs) > 0:
            lines.extend(self._calculate_big_arch_middle_purlin(sequence))
            sequence += 100
        
        # Calculate Small Arch Middle Purlin Clamps
        if project.arch_middle_purlin_small_arch != '0' and int(project.arch_middle_purlin_small_arch_pcs) > 0:
            lines.extend(self._calculate_small_arch_middle_purlin(sequence))
        
        return lines
    
    def _calculate_big_arch_middle_purlin(self, sequence):
        """Calculate Big Arch Middle Purlin Clamps"""
        lines = []
        project = self.green_master_id
        
        config_value = project.arch_middle_purlin_big_arch
        pcs_value = int(project.arch_middle_purlin_big_arch_pcs)
        
        # Get component count
        no_arch_middle_purlin_big_arch = 0
        arch_middle_purlin = project.lower_component_ids.filtered(
            lambda c: c.name == 'Arch Middle Purlin Big Arch'
        )
        if arch_middle_purlin:
            no_arch_middle_purlin_big_arch = arch_middle_purlin.nos
        
        # Get Big Arch pipe size
        big_arch_size = project._get_big_arch_data()['size']
        
        if not big_arch_size or no_arch_middle_purlin_big_arch == 0:
            return lines
        
        # Calculate Full Clamps
        full_qty = 0
        full_formula = ""
        
        if config_value == '1':  # 4 Corners
            full_qty = no_arch_middle_purlin_big_arch * 2
            full_formula = f"{no_arch_middle_purlin_big_arch} × 2"
        elif config_value == '2':  # Front & Back
            full_qty = no_arch_middle_purlin_big_arch * 2
            full_formula = f"{no_arch_middle_purlin_big_arch} × 2"
        elif config_value == '3':  # Both Sides
            full_qty = 4 * pcs_value
            full_formula = f"4 × {pcs_value}"
        elif config_value == '4':  # 4 Sides
            full_qty = ((((project.no_of_spans - 2) * 4) + 4) * pcs_value)
            full_formula = f"(((({project.no_of_spans} - 2) × 4) + 4) × {pcs_value})"
        elif config_value == '5':  # All
            full_qty = project.no_of_spans * 2
            full_formula = f"{project.no_of_spans} × 2"
        
        if full_qty > 0:
            config_name = dict(project._fields['arch_middle_purlin_big_arch'].selection)[config_value]
            lines.append({
                'wizard_id': self.id,
                'sequence': sequence,
                'category': 'ARCH MIDDLE PURLIN - BIG ARCH',
                'component': f'Full Clamps ({config_name})',
                'clamp_type': 'Full Clamp',
                'size': big_arch_size,
                'quantity': int(full_qty),
                'formula': full_formula,
                'unit_price': self._get_clamp_unit_price('Full Clamp', big_arch_size),
            })
            sequence += 10
        
        # Calculate Half Clamps (only for specific configurations)
        half_qty = 0
        half_formula = ""
        
        if config_value == '3':  # Both Sides
            half_qty = (no_arch_middle_purlin_big_arch * 2) - (4 * pcs_value)
            half_formula = f"({no_arch_middle_purlin_big_arch} × 2) - (4 × {pcs_value})"
        elif config_value == '4':  # 4 Sides
            half_qty = no_arch_middle_purlin_big_arch - (((((project.no_of_spans - 2) * 4) + 4) * pcs_value) / 2)
            half_formula = f"{no_arch_middle_purlin_big_arch} - ((((({project.no_of_spans} - 2) × 4) + 4) × {pcs_value}) / 2)"
        elif config_value == '5':  # All
            half_qty = project.no_of_spans * (project.no_of_bays - 1)
            half_formula = f"{project.no_of_spans} × ({project.no_of_bays} - 1)"
        
        if half_qty > 0:
            config_name = dict(project._fields['arch_middle_purlin_big_arch'].selection)[config_value]
            lines.append({
                'wizard_id': self.id,
                'sequence': sequence,
                'category': 'ARCH MIDDLE PURLIN - BIG ARCH',
                'component': f'Half Clamps ({config_name})',
                'clamp_type': 'Half Clamp',
                'size': big_arch_size,
                'quantity': int(half_qty),
                'formula': half_formula,
                'unit_price': self._get_clamp_unit_price('Half Clamp', big_arch_size),
            })
        
        return lines
    
    def _calculate_small_arch_middle_purlin(self, sequence):
        """Calculate Small Arch Middle Purlin Clamps"""
        lines = []
        project = self.green_master_id
        
        config_value = project.arch_middle_purlin_small_arch
        pcs_value = int(project.arch_middle_purlin_small_arch_pcs)
        
        # Get component count
        no_arch_middle_purlin_small_arch = 0
        arch_middle_purlin = project.lower_component_ids.filtered(
            lambda c: c.name == 'Arch Middle Purlin Small Arch'
        )
        if arch_middle_purlin:
            no_arch_middle_purlin_small_arch = arch_middle_purlin.nos
        
        # Get Small Arch pipe size
        small_arch_size = project._get_small_arch_data()['size']
        
        if not small_arch_size or no_arch_middle_purlin_small_arch == 0:
            return lines
        
        # Calculate Full Clamps
        full_qty = 0
        full_formula = ""
        
        if config_value == '1':  # 4 Corners
            full_qty = no_arch_middle_purlin_small_arch * 2
            full_formula = f"{no_arch_middle_purlin_small_arch} × 2"
        elif config_value == '2':  # Front & Back
            full_qty = no_arch_middle_purlin_small_arch * 2
            full_formula = f"{no_arch_middle_purlin_small_arch} × 2"
        elif config_value == '3':  # Both Sides
            full_qty = 4 * pcs_value
            full_formula = f"4 × {pcs_value}"
        elif config_value == '4':  # 4 Sides
            full_qty = ((((project.no_of_spans - 2) * 4) + 4) * pcs_value)
            full_formula = f"(((({project.no_of_spans} - 2) × 4) + 4) × {pcs_value})"
        elif config_value == '5':  # All
            full_qty = project.no_of_spans * 2
            full_formula = f"{project.no_of_spans} × 2"
        
        if full_qty > 0:
            config_name = dict(project._fields['arch_middle_purlin_small_arch'].selection)[config_value]
            lines.append({
                'wizard_id': self.id,
                'sequence': sequence,
                'category': 'ARCH MIDDLE PURLIN - SMALL ARCH',
                'component': f'Full Clamps ({config_name})',
                'clamp_type': 'Full Clamp',
                'size': small_arch_size,
                'quantity': int(full_qty),
                'formula': full_formula,
                'unit_price': self._get_clamp_unit_price('Full Clamp', small_arch_size),
            })
            sequence += 10
        
        # Calculate Half Clamps (only for specific configurations)
        half_qty = 0
        half_formula = ""
        
        if config_value == '3':  # Both Sides
            half_qty = (no_arch_middle_purlin_small_arch * 2) - (4 * pcs_value)
            half_formula = f"({no_arch_middle_purlin_small_arch} × 2) - (4 × {pcs_value})"
        elif config_value == '4':  # 4 Sides
            half_qty = no_arch_middle_purlin_small_arch - (((((project.no_of_spans - 2) * 4) + 4) * pcs_value) / 2)
            half_formula = f"{no_arch_middle_purlin_small_arch} - ((((({project.no_of_spans} - 2) × 4) + 4) × {pcs_value}) / 2)"
        elif config_value == '5':  # All
            half_qty = project.no_of_spans * (project.no_of_bays - 1)
            half_formula = f"{project.no_of_spans} × ({project.no_of_bays} - 1)"
        
        if half_qty > 0:
            config_name = dict(project._fields['arch_middle_purlin_small_arch'].selection)[config_value]
            lines.append({
                'wizard_id': self.id,
                'sequence': sequence,
                'category': 'ARCH MIDDLE PURLIN - SMALL ARCH',
                'component': f'Half Clamps ({config_name})',
                'clamp_type': 'Half Clamp',
                'size': small_arch_size,
                'quantity': int(half_qty),
                'formula': half_formula,
                'unit_price': self._get_clamp_unit_price('Half Clamp', small_arch_size),
            })
        
        return lines
    
    def _get_clamp_unit_price(self, clamp_type, size):
        """Get unit price for a specific clamp type and size"""
        master_record = self.env['accessories.master'].search([
            ('name', '=', clamp_type),
            ('category', '=', 'clamps'),
            ('size_specification', '=', size),
            ('active', '=', True)
        ], limit=1)
        
        return master_record.unit_price if master_record else 0.0
    
    def action_export_excel(self):
        """Export clamp calculation details to Excel"""
        # First calculate if not done
        if not self.calculation_line_ids:
            self.calculate_clamps()
        
        # Create Excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Clamp Calculations')
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        category_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9E2F3',
            'border': 1
        })
        
        data_format = workbook.add_format({
            'border': 1,
            'align': 'left'
        })
        
        number_format = workbook.add_format({
            'border': 1,
            'align': 'right'
        })
        
        currency_format = workbook.add_format({
            'border': 1,
            'align': 'right',
            'num_format': '#,##0.00'
        })
        
        # Set column widths
        worksheet.set_column('A:A', 25)  # Category
        worksheet.set_column('B:B', 30)  # Component
        worksheet.set_column('C:C', 15)  # Clamp Type
        worksheet.set_column('D:D', 12)  # Size
        worksheet.set_column('E:E', 10)  # Quantity
        worksheet.set_column('F:F', 40)  # Formula
        worksheet.set_column('G:G', 12)  # Unit Price
        worksheet.set_column('H:H', 15)  # Total Cost
        
        # Write headers
        headers = ['Category', 'Component', 'Clamp Type', 'Size', 'Quantity', 'Formula/Notes', 'Unit Price', 'Total Cost']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Write data
        row = 1
        current_category = None
        
        for line in self.calculation_line_ids:
            # Add category row if changed
            if line.category != current_category:
                worksheet.merge_range(row, 0, row, 7, line.category, category_format)
                current_category = line.category
                row += 1
            
            # Write line data
            worksheet.write(row, 0, '', data_format)  # Category column (empty for data rows)
            worksheet.write(row, 1, line.component, data_format)
            worksheet.write(row, 2, line.clamp_type, data_format)
            worksheet.write(row, 3, line.size, data_format)
            worksheet.write(row, 4, line.quantity, number_format)
            worksheet.write(row, 5, line.formula or '', data_format)
            worksheet.write(row, 6, line.unit_price, currency_format)
            worksheet.write(row, 7, line.total_cost, currency_format)
            row += 1
        
        # Add totals row
        row += 1
        worksheet.merge_range(row, 0, row, 3, 'GRAND TOTAL', header_format)
        worksheet.write(row, 4, self.total_quantity, number_format)
        worksheet.write(row, 5, '', data_format)
        worksheet.write(row, 6, '', data_format)
        worksheet.write(row, 7, self.total_cost, currency_format)
        
        # Add project information
        row += 3
        worksheet.write(row, 0, 'Project:', header_format)
        worksheet.merge_range(row, 1, row, 3, self.green_master_id.customer or 'N/A', data_format)
        row += 1
        worksheet.write(row, 0, 'Calculation Date:', header_format)
        worksheet.merge_range(row, 1, row, 3, self.calculation_date.strftime('%Y-%m-%d %H:%M:%S'), data_format)
        
        workbook.close()
        output.seek(0)
        
        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': f'Clamp_Calculations_{self.green_master_id.customer or "Project"}_{fields.Datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        
        output.close()
        
        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }


class ClampCalculationDetailLine(models.TransientModel):
    _name = 'clamp.calculation.detail.line'
    _description = 'Clamp Calculation Detail Line'
    _order = 'sequence, category, component'
    
    wizard_id = fields.Many2one('clamp.calculation.detail', string='Wizard', required=True, ondelete='cascade')
    sequence = fields.Integer('Sequence', default=10)
    
    # Calculation details
    category = fields.Char('Category', required=True)
    component = fields.Char('Component', required=True)
    clamp_type = fields.Char('Clamp Type', required=True)
    size = fields.Char('Size', required=True)
    quantity = fields.Integer('Quantity', default=0)
    formula = fields.Text('Formula/Notes')
    
    # Pricing
    unit_price = fields.Float('Unit Price', default=0.0)
    total_cost = fields.Float('Total Cost', compute='_compute_total_cost', store=True)
    
    @api.depends('quantity', 'unit_price')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.quantity * record.unit_price