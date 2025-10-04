# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from math import ceil
import logging

_logger = logging.getLogger(__name__)

class GreenMasterClamps(models.Model):
    _inherit = 'green.master'
    
    # Clamp configuration fields
    clamp_type = fields.Selection([
        ('w_type', 'W Type'),
        ('m_type', 'M Type'),
        ('none', 'None')
    ], string='Clamp Type', default='none', tracking=True)
    
    # Purlin clamp configurations for W Type
    big_purlin_clamp_type_first = fields.Selection([
        ('full_clamp', 'Full Clamp'),
        ('l_joint', 'L Joint'),
    ], string='Big Purlin First Type', tracking=True)
    
    big_purlin_clamp_type_second = fields.Selection([
        ('half_clamp', 'Half Clamp'),
        ('t_joint', 'T Joint'),
    ], string='Big Purlin Second Type', tracking=True)
    
    small_purlin_clamp_type_first = fields.Selection([
        ('full_clamp', 'Full Clamp'),
        ('l_joint', 'L Joint'),
    ], string='Small Purlin First Type', tracking=True)
    
    small_purlin_clamp_type_second = fields.Selection([
        ('half_clamp', 'Half Clamp'),
        ('t_joint', 'T Joint'),
    ], string='Small Purlin Second Type', tracking=True)
    
    # Bottom chord clamp type for M Type
    bottom_chord_clamp_type = fields.Selection([
        ('single', 'Single'),
        ('triple', 'Triple')
    ], string='Bottom Chord Clamp Type', default='single', tracking=True)
    
    # Summary fields
    clamps_size_summary = fields.Text(
        string='Clamps Size Summary',
        compute='_compute_clamps_size_summary',
        store=False
    )
    
    border_purlin_clamps_summary = fields.Text(
        string='Border Purlin Clamps Summary',
        compute='_compute_border_purlin_clamps_summary',
        store=False
    )
    
    # Override base field to add size override capability
    clamps_component_ids = fields.One2many(
        'accessories.component.line',
        'green_master_id',
        domain=[('section', '=', 'clamps')],
        string='Clamps Components'
    )
    
    @api.depends('clamps_component_ids', 'clamps_component_ids.size_specification', 'clamps_component_ids.nos')
    def _compute_clamps_size_summary(self):
        """Compute summary of clamp sizes"""
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
    
    @api.depends('bay_side_border_purlin', 'span_side_border_purlin')
    def _compute_border_purlin_clamps_summary(self):
        """Compute border purlin clamps summary"""
        for record in self:
            if int(record.bay_side_border_purlin or 0) == 0 and int(record.span_side_border_purlin or 0) == 0:
                record.border_purlin_clamps_summary = ""
                continue
            
            summary_parts = []
            if int(record.bay_side_border_purlin or 0) > 0:
                summary_parts.append(f"Bay Side Border: {record.bay_side_border_purlin}")
            if int(record.span_side_border_purlin or 0) > 0:
                summary_parts.append(f"Span Side Border: {record.span_side_border_purlin}")
            if hasattr(record, 'no_anchor_frame_lines') and record.no_anchor_frame_lines > 0:
                summary_parts.append(f"Anchor Frames: {record.no_anchor_frame_lines}")
            
            record.border_purlin_clamps_summary = " | ".join(summary_parts) if summary_parts else "No border purlins"
    
    def _calculate_all_accessories(self):
        """Extend to add clamp calculations"""
        super()._calculate_all_accessories()
        self._calculate_clamp_components()
    
    def _calculate_clamp_components(self):
        """Calculate all clamp components"""
        # Clear existing clamp components
        self.clamps_component_ids.unlink()
        
        # Calculate advanced clamps
        self._calculate_advanced_clamps()
    
    def _calculate_advanced_clamps(self):
        """Main method for advanced clamp calculations"""
        # Check if any clamps are needed
        if (self.clamp_type == 'none' and 
            not (hasattr(self, 'is_side_coridoors') and self.is_side_coridoors and self.support_hockeys > 0) and
            int(self.bay_side_border_purlin or 0) <= 0 and 
            int(self.span_side_border_purlin or 0) <= 0 and
            not (hasattr(self, 'is_bottom_chord') and self.is_bottom_chord and int(self.v_support_bottom_chord_frame or 0) > 0)):
            _logger.info("No clamps configuration detected, skipping clamp calculations")
            return
        
        # Use accumulator pattern to group clamps by type and size
        clamp_accumulator = {}
        
        # W Type or M Type clamps
        if self.clamp_type == 'w_type':
            self._accumulate_w_type_clamps(clamp_accumulator)
        elif self.clamp_type == 'm_type':
            self._accumulate_m_type_clamps(clamp_accumulator)
        
        # V Support to Main Column clamps
        if hasattr(self, 'is_bottom_chord') and self.is_bottom_chord and int(self.v_support_bottom_chord_frame or 0) > 0:
            self._accumulate_v_support_main_column_clamps(clamp_accumulator)
        
        # ASC Support clamps
        if hasattr(self, 'is_side_coridoors') and self.is_side_coridoors and self.support_hockeys > 0:
            self._accumulate_asc_support_clamps(clamp_accumulator)
        
        # Border Purlin clamps
        self._accumulate_border_purlin_clamps(clamp_accumulator)
        
        # Arch Middle Purlin clamps
        self._accumulate_arch_middle_purlin_clamps(clamp_accumulator)
        
        # Create clamp components from accumulator
        self._create_clamp_components_from_accumulator(clamp_accumulator)

    
    def _accumulate_w_type_clamps(self, accumulator):
        """Accumulate W Type clamps"""
        # Get component data
        bottom_chord_data = self._get_bottom_chord_data()
        v_support_count = self._get_v_support_count()
        big_arch_data = self._get_big_arch_data()
        small_arch_data = self._get_small_arch_data()
        
        # Bottom Chord clamps
        if bottom_chord_data['count'] > 0 and bottom_chord_data['size']:
            qty = (bottom_chord_data['count'] * 3) + v_support_count
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', bottom_chord_data['size'], qty)
        
        # Big Arch clamps
        if big_arch_data['count'] > 0 and big_arch_data['size']:
            qty = big_arch_data['count'] * 2
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], qty)
        
        # Small Arch clamps
        if small_arch_data['count'] > 0 and small_arch_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_data['size'], small_arch_data['count'])
        
        # Purlin clamps based on configuration
        if big_arch_data['size']:
            if self.big_purlin_clamp_type_first:
                qty_first = self.no_of_spans * 2
                clamp_name = 'Full Clamp' if self.big_purlin_clamp_type_first == 'full_clamp' else 'L Joint'
                self._add_to_clamp_accumulator(accumulator, clamp_name, big_arch_data['size'], qty_first)
            
            if self.big_purlin_clamp_type_second:
                qty_second = big_arch_data['count'] - (self.no_of_spans * 2) if self.big_purlin_clamp_type_first else big_arch_data['count']
                if qty_second > 0:
                    clamp_name = 'Half Clamp' if self.big_purlin_clamp_type_second == 'half_clamp' else 'T Joint'
                    self._add_to_clamp_accumulator(accumulator, clamp_name, big_arch_data['size'], qty_second)
        
        if small_arch_data['size']:
            if self.small_purlin_clamp_type_first:
                qty_first = self.no_of_spans * 2
                clamp_name = 'Full Clamp' if self.small_purlin_clamp_type_first == 'full_clamp' else 'L Joint'
                self._add_to_clamp_accumulator(accumulator, clamp_name, small_arch_data['size'], qty_first)
            
            if self.small_purlin_clamp_type_second:
                qty_second = small_arch_data['count'] - (self.no_of_spans * 2) if self.small_purlin_clamp_type_first else small_arch_data['count']
                if qty_second > 0:
                    clamp_name = 'Half Clamp' if self.small_purlin_clamp_type_second == 'half_clamp' else 'T Joint'
                    self._add_to_clamp_accumulator(accumulator, clamp_name, small_arch_data['size'], qty_second)
    
    def _accumulate_m_type_clamps(self, accumulator):
        """Accumulate M Type clamps"""
        # Get component data
        bottom_chord_data = self._get_bottom_chord_data()
        v_support_count = self._get_v_support_count()
        big_arch_data = self._get_big_arch_data()
        small_arch_data = self._get_small_arch_data()
        
        # Bottom Chord clamps
        if bottom_chord_data['count'] > 0 and bottom_chord_data['size']:
            if self.bottom_chord_clamp_type == 'single':
                qty = (bottom_chord_data['count'] * 3) + v_support_count
            else:  # triple
                qty = (bottom_chord_data['count'] * 5) + v_support_count
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', bottom_chord_data['size'], qty)
        
        # Big Arch clamps
        if big_arch_data['count'] > 0 and big_arch_data['size']:
            qty = big_arch_data['count'] * 2
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], qty)
        
        # Small Arch clamps
        if small_arch_data['count'] > 0 and small_arch_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_data['size'], small_arch_data['count'])
    
    def _accumulate_v_support_main_column_clamps(self, accumulator):
        """Accumulate V Support to Main Column clamps"""
        # This would need actual implementation based on v_support configuration
        pass
    
    def _accumulate_asc_support_clamps(self, accumulator):
        """Accumulate ASC Support clamps"""
        # Get ASC pipe size
        asc_pipe_size = self._get_asc_pipe_size()
        if asc_pipe_size and self.support_hockeys > 0:
            # Calculate total ASC support pipes
            asc_support_count = self._get_asc_support_pipes_count()
            if asc_support_count > 0:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', asc_pipe_size, asc_support_count)
    
    def _accumulate_border_purlin_clamps(self, accumulator):
        """Accumulate border purlin clamps"""
        # Implementation would go here based on border purlin configuration
        pass
    
    def _accumulate_arch_middle_purlin_clamps(self, accumulator):
        """Accumulate arch middle purlin clamps"""
        # Implementation would go here based on arch middle purlin configuration
        pass
    
    def _add_to_clamp_accumulator(self, accumulator, clamp_type, size, quantity):
        """Add clamps to accumulator"""
        if quantity <= 0:
            return
        
        key = (clamp_type, size)
        if key in accumulator:
            accumulator[key] += quantity
        else:
            accumulator[key] = quantity
    
    def _create_clamp_components_from_accumulator(self, accumulator):
        """Create clamp components from accumulator"""
        for (clamp_type, size), quantity in accumulator.items():
            # Find matching master record
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
            _logger.info(f"Created clamp component: {component_name} - Qty: {quantity}")

    
    # Helper methods to get component data
    def _get_bottom_chord_data(self):
        """Get bottom chord component data"""
        bottom_chord = self.truss_component_ids.filtered(
            lambda c: 'Bottom Chord' in c.name and 'Female' not in c.name and 'V Support' not in c.name
        )
        
        data = {'count': 0, 'size': None}
        if bottom_chord:
            data['count'] = sum(bottom_chord.mapped('nos'))
            for component in bottom_chord:
                if component.pipe_id and component.pipe_id.pipe_size:
                    data['size'] = f"{component.pipe_id.pipe_size.size_in_mm:.0f}mm"
                    break
        
        return data
    
    def _get_v_support_count(self):
        """Get V support count"""
        v_support = self.truss_component_ids.filtered(lambda c: c.name == 'V Support Bottom Chord')
        return v_support.nos if v_support else 0
    
    def _get_big_arch_data(self):
        """Get big arch data"""
        big_arch = self.truss_component_ids.filtered(lambda c: c.name == 'Big Arch')
        data = {'count': 0, 'size': None}
        if big_arch:
            data['count'] = big_arch.nos
            if big_arch.pipe_id and big_arch.pipe_id.pipe_size:
                data['size'] = f"{big_arch.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return data
    
    def _get_small_arch_data(self):
        """Get small arch data"""
        small_arch = self.truss_component_ids.filtered(lambda c: c.name == 'Small Arch')
        data = {'count': 0, 'size': None}
        if small_arch:
            data['count'] = small_arch.nos
            if small_arch.pipe_id and small_arch.pipe_id.pipe_size:
                data['size'] = f"{small_arch.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return data
    
    def _get_asc_pipe_size(self):
        """Get ASC pipe size"""
        if hasattr(self, 'asc_component_ids'):
            asc_pipes = self.asc_component_ids.filtered(lambda c: 'ASC Pipes' in c.name)
            if asc_pipes and asc_pipes[0].pipe_id and asc_pipes[0].pipe_id.pipe_size:
                return f"{asc_pipes[0].pipe_id.pipe_size.size_in_mm:.0f}mm"
        return None
    
    def _get_asc_support_pipes_count(self):
        """Get ASC support pipes count"""
        if hasattr(self, 'asc_component_ids'):
            asc_support = self.asc_component_ids.filtered(lambda c: c.name == 'ASC Pipe Support')
            return asc_support.nos if asc_support else 0
        return 0
    
    def get_clamp_calculation_details(self):
        """Get detailed clamp calculations for display"""
        details = []
        sequence = 10
        
        # M Type or W Type clamps
        if self.clamp_type == 'm_type':
            details.extend(self._get_m_type_clamp_details(sequence))
            sequence += 100
        elif self.clamp_type == 'w_type':
            details.extend(self._get_w_type_clamp_details(sequence))
            sequence += 100
        
        # Add other clamp categories details...
        
        return details
    
    def _get_m_type_clamp_details(self, sequence):
        """Get M Type clamp calculation details"""
        details = []
        bottom_chord_data = self._get_bottom_chord_data()
        v_support = self._get_v_support_count()
        
        if bottom_chord_data['count'] > 0 and bottom_chord_data['size']:
            multiplier = 3 if self.bottom_chord_clamp_type == 'single' else 5
            qty = (bottom_chord_data['count'] * multiplier) + v_support
            details.append({
                'sequence': sequence,
                'category': 'M TYPE CLAMPS',
                'component': f"Bottom Chord ({self.bottom_chord_clamp_type.title()})",
                'clamp_type': 'Full Clamp',
                'size': bottom_chord_data['size'],
                'quantity': int(qty),
                'formula': f"({bottom_chord_data['count']} × {multiplier}) + {v_support}",
                'unit_price': self._get_clamp_price('Full Clamp', bottom_chord_data['size']),
            })
        
        return details
    
    def _get_w_type_clamp_details(self, sequence):
        """Get W Type clamp calculation details"""
        details = []
        # Similar implementation for W Type details
        return details
    
    def _get_clamp_price(self, clamp_type, size):
        """Get clamp price from master data"""
        master_record = self.env['accessories.master'].search([
            ('name', '=', clamp_type),
            ('category', '=', 'clamps'),
            ('size_specification', '=', size),
            ('active', '=', True)
        ], limit=1)
        return master_record.unit_price if master_record else 0.0
    
    @api.onchange('clamp_type')
    def _onchange_clamp_type(self):
        """Handle clamp type change"""
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
        elif self.clamp_type == 'm_type':
            if not self.bottom_chord_clamp_type:
                self.bottom_chord_clamp_type = 'single'
            self.big_purlin_clamp_type_first = False
            self.big_purlin_clamp_type_second = False
            self.small_purlin_clamp_type_first = False
            self.small_purlin_clamp_type_second = False
    
    def action_view_clamp_details(self):
        """Open clamp calculation details wizard"""
        wizard = self.env['clamp.calculation.detail'].create({
            'green_master_id': self.id,
        })
        wizard.calculate_clamps()
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Clamp Calculation Details',
            'res_model': 'clamp.calculation.detail',
            'res_id': wizard.id,
            'view_mode': 'form',
            'view_id': self.env.ref('green2_accessories_clamps.view_clamp_calculation_detail_form').id,
            'target': 'new',
            'context': self.env.context,
        }
