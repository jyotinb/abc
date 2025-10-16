# -*- coding: utf-8 -*-
from odoo import models, fields, api
from math import ceil
import logging

_logger = logging.getLogger(__name__)

class GreenMasterNutbolts(models.Model):
    _inherit = 'green.master'
    
    enable_nutbolts = fields.Boolean('Calculate Nut Bolts', default=False, tracking=True)
    arch_pressed = fields.Boolean('Archs Pressed', default=False, tracking=True)
    bottom_pressed = fields.Boolean('Bottom Pressed', default=False, tracking=True)
    ippf_width = fields.Selection([('400', '400mm'), ('500', '500mm')], string='IPPF Width', default='400')
    last_span_gutter = fields.Boolean('Last Span Gutter', default=False, tracking=True)
    
    nutbolts_component_ids = fields.One2many(
        'accessories.component.line',
        'green_master_id',
        domain=[('section', '=', 'nutbolts')],
        string='Nut-Bolt Components'
    )
    
    total_nutbolts_cost = fields.Float('Total Nut-Bolts Cost', compute='_compute_accessories_totals', store=True)
    
    AVAILABLE_BOLT_SIZES = [(10, 40), (10, 50), (10, 60), (10, 80), (10, 100), (10, 120), (6, 20)]
    
    @api.depends('nutbolts_component_ids.total_cost')
    def _compute_accessories_totals(self):
        super()._compute_accessories_totals()
        for record in self:
            record.total_nutbolts_cost = sum(record.nutbolts_component_ids.mapped('total_cost'))
            record.total_accessories_cost += record.total_nutbolts_cost
    
    def _calculate_all_accessories(self):
        super()._calculate_all_accessories()
        if self.enable_nutbolts:
            self._calculate_nutbolt_components()
    
    def _calculate_nutbolt_components(self):
        _logger.info("Starting nut-bolt calculations")
        self.nutbolts_component_ids.unlink()  # Clear existing
        
        self._calculate_column_nutbolts()
        self._calculate_bracket_nutbolts()
        self._calculate_clamp_nutbolts()
        self._calculate_bottom_chord_nutbolts()
        self._calculate_side_screen_guard_nutbolts()
        self._calculate_ippf_nutbolts()
        self._calculate_ippf_drainage_nutbolts()
        self._calculate_tjoint_nutbolts()
        self._calculate_ljoint_nutbolts()
        self._calculate_gi_patti_nutbolts()
        
        _logger.info("Nut-bolt calculations completed")
    
    def _round_to_available_bolt_size(self, calculated_length, diameter=10):
        """Round up to nearest available bolt size"""
        for bolt_diameter, bolt_length in self.AVAILABLE_BOLT_SIZES:
            if bolt_diameter == diameter and calculated_length <= bolt_length:
                return f"{bolt_diameter}x{bolt_length}"
        max_sizes = [length for d, length in self.AVAILABLE_BOLT_SIZES if d == diameter]
        if max_sizes:
            return f"{diameter}x{max(max_sizes)}"
        return f"{diameter}x{calculated_length}"
    
    def _get_pipe_size_from_component(self, component_name, section='frame'):
        """Get pipe size from a component"""
        component_ids = getattr(self, f'{section}_component_ids', False)
        if not component_ids:
            return 0
        component = component_ids.filtered(lambda c: c.name == component_name)
        if component and component.pipe_id and component.pipe_id.pipe_size:
            return component.pipe_id.pipe_size.size_in_mm
        return 0
    
    def _get_component_nos(self, component_name, section='frame'):
        """Get number of components"""
        component_ids = getattr(self, f'{section}_component_ids', False)
        if not component_ids:
            return 0
        component = component_ids.filtered(lambda c: c.name == component_name)
        return component.nos if component else 0
    
    def _create_nutbolt_component(self, name, size_spec, quantity):
        """Create a nut-bolt component line"""
        if quantity <= 0:
            return None
        try:
            master_record = self.env['accessories.master'].search([
                ('name', '=', f'Nut Bolt {size_spec}'),
                ('category', '=', 'nutbolts'),
                ('active', '=', True)
            ], limit=1)
            
            vals = {
                'green_master_id': self.id,
                'section': 'nutbolts',
                'name': name,
                'nos': int(quantity),
                'size_specification': size_spec,
                'unit_price': master_record.unit_price if master_record else 0.0,
                'is_calculated': True,
            }
            if master_record:
                vals['accessories_master_id'] = master_record.id
            
            component = self.env['accessories.component.line'].create(vals)
            _logger.info(f"Created nut-bolt: {name} - Size: {size_spec} - Qty: {quantity}")
            return component
        except Exception as e:
            _logger.error(f"Error creating nut-bolt {name}: {e}")
            return None
    
    def _calculate_column_nutbolts(self):
        """Calculate nut-bolts for columns"""
        column_types = [
            ('Middle Columns', 'Middle Column'),
            ('Main Columns', 'Main Column'),
            ('Thick Columns', 'Thick Column'),
        ]
        for component_name, display_name in column_types:
            component = self.frame_component_ids.filtered(lambda c: c.name == component_name)
            if component and component.nos > 0:
                pipe_size = self._get_pipe_size_from_component(component_name, 'frame')
                if pipe_size > 0:
                    calculated_length = ceil(pipe_size + 15)
                    size_spec = self._round_to_available_bolt_size(calculated_length)
                    quantity = component.nos * 2
                    self._create_nutbolt_component(f'Nut Bolt {size_spec} - {display_name}', size_spec, quantity)
    
    def _calculate_bracket_nutbolts(self):
        """Calculate nut-bolts for all bracket types"""
        # Full Gutter Arch Bracket HDGI 5.0 MM
        self._calculate_full_bracket_nutbolts()
        
        # Half Left Bracket
        self._calculate_half_bracket_nutbolts('Gutter Arch Bracket HDGI Half Left', 'Half Left')
        
        # Half Right Bracket
        self._calculate_half_bracket_nutbolts('Gutter Arch Bracket HDGI Half Right', 'Half Right')
    
    def _calculate_full_bracket_nutbolts(self):
        """Calculate nut-bolts for full gutter arch bracket"""
        bracket = self.brackets_component_ids.filtered(lambda c: c.name == 'Gutter Arch Bracket HDGI 5.0 MM')
        if not bracket or bracket.nos <= 0:
            return
        
        # Arch bolts (4 per bracket)
        arch_pipe_size = self._get_pipe_size_from_component('Big Arch', 'truss')
        if self.arch_pressed:
            arch_size = '10x40'
        else:
            calculated_length = ceil(arch_pipe_size + 15) if arch_pipe_size > 0 else 40
            arch_size = self._round_to_available_bolt_size(calculated_length)
        self._create_nutbolt_component(f'Nut Bolt {arch_size} - Full Bracket Arch', arch_size, bracket.nos * 4)
        
        # Bottom bolts (2 per bracket)
        bottom_pipe_size = self._get_pipe_size_from_component('Bottom Chord Inner Line', 'truss')
        if self.bottom_pressed:
            bottom_size = '10x40'
        else:
            calculated_length = ceil(bottom_pipe_size + 15) if bottom_pipe_size > 0 else 40
            bottom_size = self._round_to_available_bolt_size(calculated_length)
        self._create_nutbolt_component(f'Nut Bolt {bottom_size} - Full Bracket Bottom', bottom_size, bracket.nos * 2)
        
        # Column bolts (2 per bracket)
        column_pipe_size = self._get_pipe_size_from_component('Main Columns', 'frame')
        if column_pipe_size > 0:
            calculated_length = ceil(column_pipe_size + 15)
            column_size = self._round_to_available_bolt_size(calculated_length)
            self._create_nutbolt_component(f'Nut Bolt {column_size} - Full Bracket Column', column_size, bracket.nos * 2)
    
    def _calculate_half_bracket_nutbolts(self, bracket_name, display_name):
        """Calculate nut-bolts for half brackets (Left/Right)"""
        bracket = self.brackets_component_ids.filtered(lambda c: c.name == bracket_name)
        if not bracket or bracket.nos <= 0:
            return
        
        # Arch bolts (2 per bracket)
        arch_pipe_size = self._get_pipe_size_from_component('Big Arch', 'truss')
        if self.arch_pressed:
            arch_size = '10x40'
        else:
            calculated_length = ceil(arch_pipe_size + 15) if arch_pipe_size > 0 else 40
            arch_size = self._round_to_available_bolt_size(calculated_length)
        self._create_nutbolt_component(f'Nut Bolt {arch_size} - {display_name} Bracket Arch', arch_size, bracket.nos * 2)
        
        # Bottom bolts (2 per bracket)
        bottom_pipe_size = self._get_pipe_size_from_component('Bottom Chord Inner Line', 'truss')
        if self.bottom_pressed:
            bottom_size = '10x40'
        else:
            calculated_length = ceil(bottom_pipe_size + 15) if bottom_pipe_size > 0 else 40
            bottom_size = self._round_to_available_bolt_size(calculated_length)
        self._create_nutbolt_component(f'Nut Bolt {bottom_size} - {display_name} Bracket Bottom', bottom_size, bracket.nos * 2)
        
        # Column bolts (2 per bracket)
        column_pipe_size = self._get_pipe_size_from_component('Main Columns', 'frame')
        if column_pipe_size > 0:
            calculated_length = ceil(column_pipe_size + 15)
            column_size = self._round_to_available_bolt_size(calculated_length)
            self._create_nutbolt_component(f'Nut Bolt {column_size} - {display_name} Bracket Column', column_size, bracket.nos * 2)
    
    def _calculate_clamp_nutbolts(self):
        """Calculate nut-bolts for clamps"""
        # Full Clamps - 1 bolt each
        full_clamps = self.clamps_component_ids.filtered(lambda c: 'Full Clamp' in c.name)
        for clamp in full_clamps:
            if clamp.nos > 0:
                self._create_nutbolt_component('Nut Bolt 10x40 - Full Clamp', '10x40', clamp.nos)
        
        # Half Clamps - 2 bolts each
        half_clamps = self.clamps_component_ids.filtered(lambda c: 'Half Clamp' in c.name)
        for clamp in half_clamps:
            if clamp.nos > 0:
                self._create_nutbolt_component('Nut Bolt 10x40 - Half Clamp', '10x40', clamp.nos * 2)
    
    def _calculate_bottom_chord_nutbolts(self):
        """Calculate nut-bolts for bottom chord inner line male"""
        component = self.truss_component_ids.filtered(lambda c: 'Bottom Chord Inner Line Male' in c.name)
        if component and component.nos > 0:
            pipe_size = self._get_pipe_size_from_component('Bottom Chord Inner Line Male', 'truss')
            if pipe_size > 0:
                calculated_length = ceil(pipe_size + 10)
                size_spec = self._round_to_available_bolt_size(calculated_length)
                self._create_nutbolt_component(f'Nut Bolt {size_spec} - Bottom Chord Male', size_spec, component.nos)
    
    def _calculate_side_screen_guard_nutbolts(self):
        """Calculate nut-bolts for side screen guard"""
        if not hasattr(self, 'sidescreen_component_ids'):
            return
        
        component = self.sidescreen_component_ids.filtered(lambda c: 'Side Screen Guard' in c.name)
        if not component or component.nos <= 0:
            return
        
        # Get spacer length
        spacer = self.sidescreen_component_ids.filtered(lambda c: 'Side Screen Guard Spacer' in c.name)
        spacer_length = 0
        if spacer and spacer.pipe_id and spacer.pipe_id.length:
            spacer_length = spacer.pipe_id.length
        
        # Check for ASC
        asc_component = self.frame_component_ids.filtered(lambda c: 'ASC' in c.name and c.nos > 0)
        
        if asc_component:
            # Use ASC pipe size
            asc_pipe_size = asc_component[0].pipe_id.pipe_size.size_in_mm if asc_component[0].pipe_id and asc_component[0].pipe_id.pipe_size else 0
            if asc_pipe_size > 0:
                calculated_length = ceil(asc_pipe_size + spacer_length + 10)
                size_spec = self._round_to_available_bolt_size(calculated_length)
                self._create_nutbolt_component(f'Nut Bolt {size_spec} - Side Screen Guard', size_spec, component.nos)
        else:
            # Use Main Column pipe size
            main_column_size = self._get_pipe_size_from_component('Main Columns', 'frame')
            if main_column_size > 0:
                calculated_length = ceil(main_column_size + spacer_length + 10)
                size_spec = self._round_to_available_bolt_size(calculated_length)
                self._create_nutbolt_component(f'Nut Bolt {size_spec} - Side Screen Guard', size_spec, component.nos)
    
    def _calculate_ippf_nutbolts(self):
        """Calculate nut-bolts for IPPF"""
        if not hasattr(self, 'ippf_component_ids'):
            return
        
        ippf_gutter = self._get_component_nos('IPPF Gutter', 'ippf')
        if ippf_gutter <= 0:
            return
        
        no_of_spans = getattr(self, 'no_of_spans', 0)
        if no_of_spans <= 0:
            return
        
        # Calculate multiplier based on last span gutter
        if self.last_span_gutter:
            multiplier = ippf_gutter + no_of_spans + 1
        else:
            multiplier = ippf_gutter + no_of_spans - 1
        
        # Based on IPPF width
        if self.ippf_width == '400':
            self._create_nutbolt_component('Nut Bolt 10x40 - IPPF', '10x40', multiplier * 4)
            self._create_nutbolt_component('Nut Bolt 6x20 - IPPF', '6x20', multiplier * 2)
        else:  # 500
            self._create_nutbolt_component('Nut Bolt 10x40 - IPPF', '10x40', multiplier * 6)
            self._create_nutbolt_component('Nut Bolt 6x20 - IPPF', '6x20', multiplier * 2)
    
    def _calculate_ippf_drainage_nutbolts(self):
        """Calculate nut-bolts for IPPF drainage extension"""
        if not hasattr(self, 'ippf_component_ids'):
            return
        
        drainage = self._get_component_nos('Gutter IPPF Drainage Extension', 'ippf')
        if drainage <= 0:
            return
        
        if self.ippf_width == '400':
            self._create_nutbolt_component('Nut Bolt 10x40 - IPPF Drainage', '10x40', drainage * 4)
            self._create_nutbolt_component('Nut Bolt 6x20 - IPPF Drainage', '6x20', drainage * 2)
        else:  # 500
            self._create_nutbolt_component('Nut Bolt 10x40 - IPPF Drainage', '10x40', drainage * 6)
            self._create_nutbolt_component('Nut Bolt 6x20 - IPPF Drainage', '6x20', drainage * 2)
    
    def _calculate_tjoint_nutbolts(self):
        """Calculate nut-bolts for T-Joint (X*Y)"""
        if not hasattr(self, 'tjoint_component_ids'):
            return
        
        for tjoint in self.tjoint_component_ids:
            if tjoint.nos <= 0:
                continue
            
            # Parse X*Y from component name or specification
            # Assuming format like "T Joint 50x40" or pipe_id contains sizes
            if tjoint.pipe_id and hasattr(tjoint.pipe_id, 'x_size') and hasattr(tjoint.pipe_id, 'y_size'):
                x_size = tjoint.pipe_id.x_size
                y_size = tjoint.pipe_id.y_size
                
                # X + 10 bolts
                x_length = ceil(x_size + 10)
                x_spec = self._round_to_available_bolt_size(x_length)
                self._create_nutbolt_component(f'Nut Bolt {x_spec} - T Joint X', x_spec, tjoint.nos)
                
                # Y + 10 bolts (2 per joint)
                y_length = ceil(y_size + 10)
                y_spec = self._round_to_available_bolt_size(y_length)
                self._create_nutbolt_component(f'Nut Bolt {y_spec} - T Joint Y', y_spec, tjoint.nos * 2)
    
    def _calculate_ljoint_nutbolts(self):
        """Calculate nut-bolts for L-Joint (X*Y)"""
        if not hasattr(self, 'ljoint_component_ids'):
            return
        
        for ljoint in self.ljoint_component_ids:
            if ljoint.nos <= 0:
                continue
            
            # Parse X*Y from component name or specification
            if ljoint.pipe_id and hasattr(ljoint.pipe_id, 'x_size') and hasattr(ljoint.pipe_id, 'y_size'):
                x_size = ljoint.pipe_id.x_size
                y_size = ljoint.pipe_id.y_size
                
                # X + 10 bolts (1 per joint)
                x_length = ceil(x_size + 10)
                x_spec = self._round_to_available_bolt_size(x_length)
                self._create_nutbolt_component(f'Nut Bolt {x_spec} - L Joint X', x_spec, ljoint.nos)
                
                # Y + 10 bolts (1 per joint)
                y_length = ceil(y_size + 10)
                y_spec = self._round_to_available_bolt_size(y_length)
                self._create_nutbolt_component(f'Nut Bolt {y_spec} - L Joint Y', y_spec, ljoint.nos)
    
    def _calculate_gi_patti_nutbolts(self):
        """Calculate nut-bolts for GI Patti"""
        if not hasattr(self, 'gipatti_component_ids'):
            return
        
        gi_patti = self.gipatti_component_ids.filtered(lambda c: 'GI Patti' in c.name)
        if not gi_patti or gi_patti.nos <= 0:
            return
        
        # 10x40 bolts
        self._create_nutbolt_component('Nut Bolt 10x40 - GI Patti', '10x40', gi_patti.nos)
        
        # Gable Purlin pipe size + 10
        gable_purlin_size = self._get_pipe_size_from_component('Gable Purlin', 'truss')
        if gable_purlin_size > 0:
            calculated_length = ceil(gable_purlin_size + 10)
            size_spec = self._round_to_available_bolt_size(calculated_length)
            self._create_nutbolt_component(f'Nut Bolt {size_spec} - GI Patti Gable', size_spec, gi_patti.nos * 4)


class AccessoriesComponentLine(models.Model):
    _inherit = 'accessories.component.line'
    
    section = fields.Selection(
        selection_add=[('nutbolts', 'Nut-Bolts & Screws')],
        ondelete={'nutbolts': 'cascade'}
    )