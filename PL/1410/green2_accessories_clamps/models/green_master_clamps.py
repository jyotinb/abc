# green2_accessories_clamps/models/green_master_clamps.py
# MAIN MODEL FILE - Field declarations, main calculation entry, and UI methods

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from math import ceil
import logging

_logger = logging.getLogger(__name__)

class GreenMasterClamps(models.Model):
    _inherit = 'green.master'
    
    # =============================================
    # FIELD DECLARATIONS
    # =============================================
    
    bay_side_border_purlin = fields.Integer(
        'Bay Side Border Purlin', 
        default=0,
        help="Number of bay side border purlins per segment (0=disabled, 1=1 per segment, 2=2 per segment)"
    )
    
    span_side_border_purlin = fields.Integer(
        'Span Side Border Purlin', 
        default=0,
        help="Number of span side border purlins per segment (0=disabled, 1=1 per segment, 2=2 per segment)"
    )
    
    clamp_type = fields.Selection([
        ('w_type', 'W Type'),
        ('m_type', 'M Type'),
        ('none', 'None')
    ], string='Clamp Type', compute='_compute_clamp_type', store=True, readonly=True,
       help="Automatically set based on Arch Support Type")
    
    arch_support_type = fields.Selection([
        ('none', 'None'),
        ('w', 'W Type'),
        ('m', 'M Type'),
        ('arch_2_bottom', 'Arch to Bottom'),
        ('arch_2_straight', 'Arch to Straight Middle')
    ], string='Arch Support Type', default='none', tracking=True)
    
    # Purlin clamp configurations
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
    
    bottom_chord_clamp_type = fields.Selection([
        ('single', 'Single'),
        ('triple', 'Triple')
    ], string='Bottom Chord Clamp Type', default='single', tracking=True)
    
    # ASC-specific fields
    bay_side_clamp_required = fields.Boolean(
        'Bay Side Clamp Required',
        default=False,
        tracking=True,
        help="For Gutter Arch Brackets: specify if bay side clamps are required"
    )
    
    # ASC side indicators (computed from ASC module)
    front_span_asc = fields.Boolean(
        'Front Span ASC',
        compute='_compute_asc_sides',
        store=True,
        help="Computed from ASC width configuration"
    )
    
    back_span_asc = fields.Boolean(
        'Back Span ASC',
        compute='_compute_asc_sides',
        store=True,
        help="Computed from ASC width configuration"
    )
    
    front_bay_asc = fields.Boolean(
        'Front Bay ASC',
        compute='_compute_asc_sides',
        store=True,
        help="Computed from ASC width configuration"
    )
    
    back_bay_asc = fields.Boolean(
        'Back Bay ASC',
        compute='_compute_asc_sides',
        store=True,
        help="Computed from ASC width configuration"
    )
    
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
    
    clamps_component_ids = fields.One2many(
        'accessories.component.line',
        'green_master_id',
        domain=[('section', '=', 'clamps')],
        string='Clamps Components'
    )
    
    # =============================================
    # COMPUTED METHODS
    # =============================================
    
    @api.depends('arch_support_type')
    def _compute_clamp_type(self):
        """Compute clamp type from arch_support_type"""
        for record in self:
            if hasattr(record, 'arch_support_type'):
                if record.arch_support_type == 'w':
                    record.clamp_type = 'w_type'
                elif record.arch_support_type == 'm':
                    record.clamp_type = 'm_type'
                else:
                    record.clamp_type = 'none'
            else:
                record.clamp_type = 'none'
    
    @api.depends('width_front_span_coridoor', 'width_back_span_coridoor',
                 'width_front_bay_coridoor', 'width_back_bay_coridoor')
    def _compute_asc_sides(self):
        """Compute which ASC sides are active based on width configuration"""
        for record in self:
            record.front_span_asc = (hasattr(record, 'width_front_span_coridoor') and 
                                     record.width_front_span_coridoor > 0)
            record.back_span_asc = (hasattr(record, 'width_back_span_coridoor') and 
                                    record.width_back_span_coridoor > 0)
            record.front_bay_asc = (hasattr(record, 'width_front_bay_coridoor') and 
                                    record.width_front_bay_coridoor > 0)
            record.back_bay_asc = (hasattr(record, 'width_back_bay_coridoor') and 
                                   record.width_back_bay_coridoor > 0)
    
    @api.depends('clamps_component_ids', 'clamps_component_ids.size_specification', 
                 'clamps_component_ids.nos')
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
    
    @api.depends('bay_side_border_purlin', 'span_side_border_purlin',
                 'front_bay_asc', 'back_bay_asc', 'front_span_asc', 'back_span_asc',
                 'thick_column', 'no_anchor_frame_lines')
    def _compute_border_purlin_clamps_summary(self):
        """Compute border purlin clamps summary"""
        for record in self:
            if int(record.bay_side_border_purlin or 0) == 0 and \
               int(record.span_side_border_purlin or 0) == 0:
                record.border_purlin_clamps_summary = ""
                continue
            
            summary_parts = []
            
            if int(record.bay_side_border_purlin or 0) > 0:
                bay_info = f"Bay Side: {record.bay_side_border_purlin}"
                if record.front_bay_asc:
                    bay_info += " (Front ASC)"
                if record.back_bay_asc:
                    bay_info += " (Back ASC)"
                summary_parts.append(bay_info)
            
            if int(record.span_side_border_purlin or 0) > 0:
                span_info = f"Span Side: {record.span_side_border_purlin}"
                if record.front_span_asc:
                    span_info += " (Front ASC)"
                if record.back_span_asc:
                    span_info += " (Back ASC)"
                summary_parts.append(span_info)
            
            if hasattr(record, 'thick_column') and record.thick_column != '0':
                thick_label = dict(record._fields['thick_column'].selection).get(
                    record.thick_column, '')
                summary_parts.append(f"Thick: {thick_label}")
            
            if hasattr(record, 'no_anchor_frame_lines') and record.no_anchor_frame_lines > 0:
                summary_parts.append(f"AF Lines: {record.no_anchor_frame_lines}")
            
            record.border_purlin_clamps_summary = " | ".join(summary_parts) if summary_parts else ""
    
    # =============================================
    # VALIDATION
    # =============================================
    
    @api.constrains('big_purlin_clamp_type_first', 'big_purlin_clamp_type_second',
                    'small_purlin_clamp_type_first', 'small_purlin_clamp_type_second')
    def _check_purlin_clamp_configuration(self):
        """Validate purlin clamp configuration"""
        for record in self:
            if record.big_purlin_clamp_type_first and not record.big_purlin_clamp_type_second:
                raise ValidationError(
                    "Big Purlin Second Type cannot be blank when First Type is selected!")
            
            if record.small_purlin_clamp_type_first and not record.small_purlin_clamp_type_second:
                raise ValidationError(
                    "Small Purlin Second Type cannot be blank when First Type is selected!")
    
    # =============================================
    # MAIN CALCULATION METHODS
    # =============================================
    
    def _calculate_all_accessories(self):
        """Extend to add clamp calculations"""
        super()._calculate_all_accessories()
        self._calculate_clamp_components()
    
    def _calculate_clamp_components(self):
        """Calculate all clamp components"""
        self.clamps_component_ids.unlink()
        self._calculate_advanced_clamps()
    
    def _calculate_advanced_clamps(self):
        """Main method for advanced clamp calculations"""
        # Import calculation modules here to avoid circular imports
        from . import clamp_calculations_standard as std_calc
        from . import clamp_calculations_special as spec_calc
        
        arch_support_type = getattr(self, 'arch_support_type', 'none')
        
        if (self.clamp_type == 'none' and 
            arch_support_type in ['none', ''] and
            int(self.bay_side_border_purlin or 0) <= 0 and 
            int(self.span_side_border_purlin or 0) <= 0 and
            not (hasattr(self, 'is_side_coridoors') and self.is_side_coridoors) and
            not (hasattr(self, 'is_bottom_chord') and self.is_bottom_chord)):
            _logger.info("No clamps configuration detected, skipping clamp calculations")
            return
        
        clamp_accumulator = {}
        
        # Standard clamp calculations (delegated to module)
        if self.clamp_type == 'w_type':
            std_calc.accumulate_w_type_clamps(self, clamp_accumulator)
        elif self.clamp_type == 'm_type':
            std_calc.accumulate_m_type_clamps(self, clamp_accumulator)
        
        if arch_support_type == 'arch_2_bottom':
            std_calc.accumulate_arch_2_bottom_clamps(self, clamp_accumulator)
        elif arch_support_type == 'arch_2_straight':
            std_calc.accumulate_arch_2_straight_clamps(self, clamp_accumulator)
        
        std_calc.accumulate_purlin_clamps(self, clamp_accumulator)
        
        if hasattr(self, 'is_bottom_chord') and self.is_bottom_chord:
            std_calc.accumulate_v_support_main_column_clamps(self, clamp_accumulator)
        
        # Special clamp calculations (delegated to module)
        spec_calc.accumulate_vent_support_small_arch_clamps(self, clamp_accumulator)
        spec_calc.accumulate_cross_bracing_clamps(self, clamp_accumulator)
        spec_calc.accumulate_border_purlin_clamps(self, clamp_accumulator)
        
        # ASC Clamps
        if hasattr(self, 'is_side_coridoors') and self.is_side_coridoors:
            spec_calc.accumulate_asc_clamps_complete(self, clamp_accumulator)
        
        # ASC Support Pipe Clamps (Part A & Part B)
        if (hasattr(self, 'support_hockeys') and self.support_hockeys > 0 and
            hasattr(self, 'is_side_coridoors') and self.is_side_coridoors):
            spec_calc.accumulate_asc_support_pipe_clamps(self, clamp_accumulator)
        
        self._create_clamp_components_from_accumulator(clamp_accumulator)
    
    def _create_clamp_components_from_accumulator(self, accumulator):
        """Create clamp component records from accumulator"""
        _logger.info("=== CREATING CLAMP COMPONENTS ===")
        
        for (clamp_identifier, size), quantity in accumulator.items():
            # Handle special component names with parentheses
            if '(' in clamp_identifier:
                base_clamp_type = clamp_identifier.split('(')[0].strip()
                component_name = clamp_identifier
            else:
                base_clamp_type = clamp_identifier
                component_name = f"{clamp_identifier} - {size}"
            
            # Search for matching master record
            master_record = self.env['accessories.master'].search([
                ('name', '=', base_clamp_type),
                ('category', '=', 'clamps'),
                ('size_specification', '=', size),
                ('active', '=', True)
            ], limit=1)
            
            vals = {
                'green_master_id': self.id,
                'section': 'clamps',
                'name': component_name,
                'nos': int(quantity),
                'size_specification': size,
                'unit_price': master_record.unit_price if master_record else 0.0,
                'is_calculated': True,
                'description': f"Auto-calculated {component_name}",
            }
            
            if master_record:
                vals['accessories_master_id'] = master_record.id
            
            self.env['accessories.component.line'].create(vals)
            _logger.info(f"  Created: {component_name} - Qty: {quantity}")
    
    # =============================================
    # UI METHODS
    # =============================================
    
    def get_clamp_calculation_details(self):
        """Get detailed clamp calculations for wizard display"""
        # Import helpers to use conversion methods
        from . import clamp_helpers as helpers
        from . import clamp_calculations_standard as std_calc
        from . import clamp_calculations_special as spec_calc
        
        details = []
        sequence = 10
        
        # Process each clamp type and collect details
        temp_accumulator = {}
        arch_support_type = getattr(self, 'arch_support_type', 'none')
        
        # M or W Type Clamps
        if self.clamp_type == 'm_type':
            std_calc.accumulate_m_type_clamps(self, temp_accumulator)
            if temp_accumulator:
                details.extend(helpers.convert_accumulator_to_details(
                    self, temp_accumulator, 'M TYPE CLAMPS', sequence))
                temp_accumulator.clear()
                sequence += 100
        elif self.clamp_type == 'w_type':
            std_calc.accumulate_w_type_clamps(self, temp_accumulator)
            if temp_accumulator:
                details.extend(helpers.convert_accumulator_to_details(
                    self, temp_accumulator, 'W TYPE CLAMPS', sequence))
                temp_accumulator.clear()
                sequence += 100
        
        # Arch Support Clamps
        if arch_support_type == 'arch_2_bottom':
            std_calc.accumulate_arch_2_bottom_clamps(self, temp_accumulator)
            if temp_accumulator:
                details.extend(helpers.convert_accumulator_to_details(
                    self, temp_accumulator, 'ARCH TO BOTTOM CLAMPS', sequence))
                temp_accumulator.clear()
                sequence += 100
        elif arch_support_type == 'arch_2_straight':
            std_calc.accumulate_arch_2_straight_clamps(self, temp_accumulator)
            if temp_accumulator:
                details.extend(helpers.convert_accumulator_to_details(
                    self, temp_accumulator, 'ARCH TO STRAIGHT CLAMPS', sequence))
                temp_accumulator.clear()
                sequence += 100
        
        # Purlin Clamps
        std_calc.accumulate_purlin_clamps(self, temp_accumulator)
        if temp_accumulator:
            details.extend(helpers.convert_accumulator_to_details(
                self, temp_accumulator, 'PURLIN CLAMPS', sequence))
            temp_accumulator.clear()
            sequence += 100
        
        # V Support Clamps
        if hasattr(self, 'is_bottom_chord') and self.is_bottom_chord:
            std_calc.accumulate_v_support_main_column_clamps(self, temp_accumulator)
            if temp_accumulator:
                details.extend(helpers.convert_accumulator_to_details(
                    self, temp_accumulator, 'V SUPPORT CLAMPS', sequence))
                temp_accumulator.clear()
                sequence += 100
        
        # Vent Support Small Arch Clamps
        spec_calc.accumulate_vent_support_small_arch_clamps(self, temp_accumulator)
        if temp_accumulator:
            details.extend(helpers.convert_accumulator_to_details(
                self, temp_accumulator, 'VENT SUPPORT CLAMPS', sequence))
            temp_accumulator.clear()
            sequence += 100
        
        # Cross Bracing Clamps
        spec_calc.accumulate_cross_bracing_clamps(self, temp_accumulator)
        if temp_accumulator:
            details.extend(helpers.convert_accumulator_to_details(
                self, temp_accumulator, 'CROSS BRACING CLAMPS', sequence))
            temp_accumulator.clear()
            sequence += 100
        
        # Border Purlin Clamps
        spec_calc.accumulate_border_purlin_clamps(self, temp_accumulator)
        if temp_accumulator:
            details.extend(helpers.convert_accumulator_to_details(
                self, temp_accumulator, 'BORDER PURLIN CLAMPS', sequence))
            temp_accumulator.clear()
            sequence += 100
        
        # ASC Clamps
        if hasattr(self, 'is_side_coridoors') and self.is_side_coridoors:
            spec_calc.accumulate_asc_clamps_complete(self, temp_accumulator)
            if temp_accumulator:
                details.extend(helpers.convert_accumulator_to_details(
                    self, temp_accumulator, 'ASC CLAMPS', sequence))
                temp_accumulator.clear()
                sequence += 100
        
        # ASC Support Pipe Clamps
        if (hasattr(self, 'support_hockeys') and self.support_hockeys > 0 and
            hasattr(self, 'is_side_coridoors') and self.is_side_coridoors):
            spec_calc.accumulate_asc_support_pipe_clamps(self, temp_accumulator)
            if temp_accumulator:
                details.extend(helpers.convert_accumulator_to_details(
                    self, temp_accumulator, 'ASC SUPPORT PIPE CLAMPS', sequence))
                temp_accumulator.clear()
                sequence += 100
        
        return details
    
    # =============================================
    # ONCHANGE METHODS
    # =============================================
    
    @api.onchange('clamp_type')
    def _onchange_clamp_type(self):
        """Handle clamp type changes"""
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
                self.big_purlin_clamp_type_second = 'half_clamp'
            if not self.small_purlin_clamp_type_first:
                self.small_purlin_clamp_type_first = 'full_clamp'
                self.small_purlin_clamp_type_second = 'half_clamp'
        elif self.clamp_type == 'm_type':
            if not self.bottom_chord_clamp_type:
                self.bottom_chord_clamp_type = 'single'
            if not self.big_purlin_clamp_type_first:
                self.big_purlin_clamp_type_first = 'full_clamp'
                self.big_purlin_clamp_type_second = 'half_clamp'
            if not self.small_purlin_clamp_type_first:
                self.small_purlin_clamp_type_first = 'full_clamp'
                self.small_purlin_clamp_type_second = 'half_clamp'
    
    @api.onchange('big_purlin_clamp_type_first')
    def _onchange_big_purlin_first(self):
        """Auto-set second type when first is selected"""
        if self.big_purlin_clamp_type_first and not self.big_purlin_clamp_type_second:
            self.big_purlin_clamp_type_second = 'half_clamp'
    
    @api.onchange('small_purlin_clamp_type_first')
    def _onchange_small_purlin_first(self):
        """Auto-set second type when first is selected"""
        if self.small_purlin_clamp_type_first and not self.small_purlin_clamp_type_second:
            self.small_purlin_clamp_type_second = 'half_clamp'
    
    # =============================================
    # ACTION METHODS
    # =============================================
    
    def action_view_clamp_details(self):
        """Open clamp calculation wizard to show detailed calculations"""
        self.ensure_one()
        
        # Create wizard record
        wizard = self.env['clamp.calculation.detail'].with_context(
            active_id=self.id).create({'green_master_id': self.id})
        
        # Calculate clamps to populate wizard
        wizard.calculate_clamps()
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Clamp Calculation Details',
            'res_model': 'clamp.calculation.detail',
            'res_id': wizard.id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'green2_accessories_clamps.view_clamp_calculation_detail_form').id,
            'target': 'new',
            'context': dict(self.env.context, active_id=self.id),
        }