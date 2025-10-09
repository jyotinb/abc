from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class GreenhouseProject(models.Model):
    _inherit = 'greenhouse.project'
    
    # =============================================
    # ARCH SUPPORT TYPE FIELD
    # =============================================
    arch_support_type = fields.Selection([
        ('none', 'None'),
        ('w', 'W'),
        ('m', 'M'),
        ('arch_2_bottom', 'Arch to Bottom Support'),
        ('arch_2_straight', 'Arch to Straight Middle')
    ], string='Arch Support Type', default='none', tracking=True,
       help="""Select arch support configuration:
       - W: All 4 arch supports compulsory
       - M: All 4 arch supports compulsory
       - Arch to Bottom Support: Both Small arch supports only
       - Arch to Straight Middle: Both Big arch supports only""")
    
    # Bottom Chord Configuration
    is_bottom_chord = fields.Boolean('Bottom Chord Required', default=False, tracking=True)
    v_support_bottom_chord_frame = fields.Selection([
        ('0', '0'),
        ('2', '2')
    ], 'V Support Bottom Chord per Frame', default='0', tracking=True)
    length_v_support_bottom_chord_frame = fields.Float('Length for V Support Bottom Chord', default=1.5)
    
    # Computed Arch Support Flags (for backward compatibility)
    is_arch_support_big = fields.Boolean('Arch Support Big (Big Arch) Required', 
                                        compute='_compute_arch_support_flags', store=True)
    is_arch_support_big_small = fields.Boolean('Arch Support Big (Small Arch) Required', 
                                              compute='_compute_arch_support_flags', store=True)
    is_arch_support_small_big_arch = fields.Boolean('Arch Support Small for Big Arch Required', 
                                                    compute='_compute_arch_support_flags', store=True)
    is_arch_support_small_small_arch = fields.Boolean('Arch Support Small for Small Arch Required', 
                                                      compute='_compute_arch_support_flags', store=True)
    
    # Arch Support Lengths
    length_arch_support_big = fields.Float('Length for Arch Support Big (Big Arch)', default=2.0)
    length_arch_support_big_small = fields.Float('Length for Arch Support Big (Small Arch)', default=2.0)
    length_arch_support_small_big_arch = fields.Float('Length for Arch Support Small (Big Arch)', default=1.5)
    length_arch_support_small_small_arch = fields.Float('Length for Arch Support Small (Small Arch)', default=1.5)
    
    # Vent Support Configuration
    no_vent_big_arch_support_frame = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2'),('3', '3')
    ], string='Vent Support for Big Arch per Frame', required=True, default='0', tracking=True)
    length_vent_big_arch_support = fields.Float('Length for Vent Support Big Arch', default=2.0)
    
    no_vent_small_arch_support_frame = fields.Selection([
        ('0', '0'),('2', '2')
    ], string='Vent Support for Small Arch per Frame', required=True, default='0', tracking=True)
    length_vent_small_arch_support = fields.Float('Length for Vent Support Small Arch', default=1.5)
    
    # Border Purlin Configuration
    bay_side_border_purlin = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2')
    ], string='Bay Side Border Purlin', required=True, default='0', tracking=True)
    
    span_side_border_purlin = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2')
    ], string='Span Side Border Purlin', required=True, default='0', tracking=True)
    
    # Gutter Type (if not in base module)
    gutter_type = fields.Selection([
        ('none', 'None'),
        ('ippf', 'IPPF'),
        ('continuous', 'Continuous'),
    ], string='Gutter Type', default='none', required=True, tracking=True)
    
    # Truss section costs
    total_truss_cost = fields.Float('Total Truss Cost', compute='_compute_truss_cost', store=True)
    
    # =============================================
    # COMPUTED METHODS
    # =============================================
    @api.depends('arch_support_type')
    def _compute_arch_support_flags(self):
        """Auto-set arch support flags based on arch_support_type"""
        for record in self:
            if record.arch_support_type in ['w', 'm']:
                # W or M: All 4 compulsory
                record.is_arch_support_big = True
                record.is_arch_support_big_small = True
                record.is_arch_support_small_big_arch = True
                record.is_arch_support_small_small_arch = True
            elif record.arch_support_type == 'arch_2_bottom':
                # Arch to Bottom: Both Small only
                record.is_arch_support_big = False
                record.is_arch_support_big_small = False
                record.is_arch_support_small_big_arch = True
                record.is_arch_support_small_small_arch = True
            elif record.arch_support_type == 'arch_2_straight':
                # Arch to Straight Middle: Both Big only
                record.is_arch_support_big = True
                record.is_arch_support_big_small = True
                record.is_arch_support_small_big_arch = False
                record.is_arch_support_small_small_arch = False
            else:  # 'none'
                record.is_arch_support_big = False
                record.is_arch_support_big_small = False
                record.is_arch_support_small_big_arch = False
                record.is_arch_support_small_small_arch = False
    
    @api.depends('component_line_ids.total_cost', 'component_line_ids.section')
    def _compute_truss_cost(self):
        for rec in self:
            truss_components = rec.component_line_ids.filtered(lambda c: c.section == 'truss')
            rec.total_truss_cost = sum(truss_components.mapped('total_cost'))
    
    @api.onchange('is_bottom_chord')
    def _onchange_is_bottom_chord(self):
        if not self.is_bottom_chord:
            self.v_support_bottom_chord_frame = '0'
    
    def _calculate_all_components(self):
        """Add truss calculations"""
        super()._calculate_all_components()
        self._calculate_truss_components()
        return True
    
    def _calculate_truss_components(self):
        """Calculate truss-specific components"""
        component_vals = []
        
        # Get frame calculations
        total_anchor_frames = self.no_anchor_frame_lines * self.no_of_spans
        total_normal_frames = (self.no_of_spans * (self.no_of_bays + 1)) - total_anchor_frames
        
        # Arch calculations
        arch_big = (self.no_of_bays + 1) * self.no_of_spans
        arch_small = arch_big
        
        # Create Arch components
        if arch_big > 0:
            component_vals.append({
                'project_id': self.id,
                'section': 'truss',
                'name': 'Big Arch',
                'nos': arch_big,
                'length': self.big_arch_length,
                'is_calculated': True,
            })
        
        if arch_small > 0:
            component_vals.append({
                'project_id': self.id,
                'section': 'truss',
                'name': 'Small Arch',
                'nos': arch_small,
                'length': self.small_arch_length,
                'is_calculated': True,
            })
        
        # Bottom Chord calculations
        if self.is_bottom_chord:
            bottom_chord_af_normal = 0
            bottom_chord_af_male = 0
            bottom_chord_af_female = 0
            bottom_chord_il_normal = 0
            bottom_chord_il_male = 0
            bottom_chord_il_female = 0
            
            if self.no_column_big_frame == '0':
                if self.span_width <= 6:
                    bottom_chord_af_normal = total_anchor_frames
                else:
                    bottom_chord_af_male = total_anchor_frames
                    bottom_chord_af_female = total_anchor_frames
            elif self.no_column_big_frame == '1':
                bottom_chord_af_normal = total_anchor_frames * 2
            elif self.no_column_big_frame == '2':
                bottom_chord_af_normal = total_anchor_frames * 3
            elif self.no_column_big_frame == '3':
                bottom_chord_af_normal = total_anchor_frames * 4
            
            if self.span_width <= 6:
                bottom_chord_il_normal = total_normal_frames
            else:
                bottom_chord_il_male = total_normal_frames
                bottom_chord_il_female = total_normal_frames
            
            # Create Bottom Chord components
            if bottom_chord_af_normal > 0:
                length_af_normal = self.span_width / (1 + int(self.no_column_big_frame))
                component_vals.append({
                    'project_id': self.id,
                    'section': 'truss',
                    'name': 'Bottom Chord Anchor Frame Singular',
                    'nos': bottom_chord_af_normal,
                    'length': length_af_normal,
                    'is_calculated': True,
                })
            
            if bottom_chord_af_male > 0:
                component_vals.append({
                    'project_id': self.id,
                    'section': 'truss',
                    'name': 'Bottom Chord Anchor Frame Male',
                    'nos': bottom_chord_af_male,
                    'length': self.span_width / 2,
                    'is_calculated': True,
                })
            
            if bottom_chord_af_female > 0:
                component_vals.append({
                    'project_id': self.id,
                    'section': 'truss',
                    'name': 'Bottom Chord Anchor Frame Female',
                    'nos': bottom_chord_af_female,
                    'length': self.span_width / 2,
                    'is_calculated': True,
                })
            
            if bottom_chord_il_normal > 0:
                component_vals.append({
                    'project_id': self.id,
                    'section': 'truss',
                    'name': 'Bottom Chord Inner Line Singular',
                    'nos': bottom_chord_il_normal,
                    'length': self.span_width,
                    'is_calculated': True,
                })
            
            if bottom_chord_il_male > 0:
                component_vals.append({
                    'project_id': self.id,
                    'section': 'truss',
                    'name': 'Bottom Chord Inner Line Male',
                    'nos': bottom_chord_il_male,
                    'length': self.span_width / 2,
                    'is_calculated': True,
                })
            
            if bottom_chord_il_female > 0:
                component_vals.append({
                    'project_id': self.id,
                    'section': 'truss',
                    'name': 'Bottom Chord Inner Line Female',
                    'nos': bottom_chord_il_female,
                    'length': self.span_width / 2,
                    'is_calculated': True,
                })
            
            # V Support components
            no_v_support = int(self.v_support_bottom_chord_frame) * total_normal_frames
            no_v_support_af = int(self.v_support_bottom_chord_frame) * total_anchor_frames
            
            if no_v_support > 0:
                component_vals.append({
                    'project_id': self.id,
                    'section': 'truss',
                    'name': 'V Support Bottom Chord',
                    'nos': no_v_support,
                    'length': self.length_v_support_bottom_chord_frame,
                    'is_calculated': True,
                })
            
            if no_v_support_af > 0:
                component_vals.append({
                    'project_id': self.id,
                    'section': 'truss',
                    'name': 'V Support Bottom Chord (AF)',
                    'nos': no_v_support_af,
                    'length': self.length_v_support_bottom_chord_frame,
                    'is_calculated': True,
                })
            
            # Arch Support Straight Middle
            arch_support_straight = arch_big - total_anchor_frames
            if arch_support_straight > 0:
                component_vals.append({
                    'project_id': self.id,
                    'section': 'truss',
                    'name': 'Arch Support Straight Middle',
                    'nos': arch_support_straight,
                    'length': self.top_ridge_height - self.column_height,
                    'is_calculated': True,
                })
        
        # Arch Support components based on type
        if self.is_arch_support_big:
            component_vals.append({
                'project_id': self.id,
                'section': 'truss',
                'name': 'Arch Support Big (Big Arch)',
                'nos': arch_big,
                'length': self.length_arch_support_big,
                'is_calculated': True,
            })
        
        if self.is_arch_support_big_small:
            component_vals.append({
                'project_id': self.id,
                'section': 'truss',
                'name': 'Arch Support Big (Small Arch)',
                'nos': arch_small,
                'length': self.length_arch_support_big_small,
                'is_calculated': True,
            })
        
        if self.is_arch_support_small_big_arch:
            component_vals.append({
                'project_id': self.id,
                'section': 'truss',
                'name': 'Arch Support Small for Big Arch',
                'nos': arch_big,
                'length': self.length_arch_support_small_big_arch,
                'is_calculated': True,
            })
        
        if self.is_arch_support_small_small_arch:
            component_vals.append({
                'project_id': self.id,
                'section': 'truss',
                'name': 'Arch Support Small for Small Arch',
                'nos': arch_small,
                'length': self.length_arch_support_small_small_arch,
                'is_calculated': True,
            })
        
        # Vent Support components
        vent_big = int(arch_big) * int(self.no_vent_big_arch_support_frame)
        if vent_big > 0:
            component_vals.append({
                'project_id': self.id,
                'section': 'truss',
                'name': 'Vent Support for Big Arch',
                'nos': vent_big,
                'length': self.length_vent_big_arch_support,
                'is_calculated': True,
            })
        
        vent_small = self.no_of_bays * self.no_of_spans * int(self.no_vent_small_arch_support_frame)
        if vent_small > 0:
            component_vals.append({
                'project_id': self.id,
                'section': 'truss',
                'name': 'Vent Support for Small Arch',
                'nos': vent_small,
                'length': self.length_vent_small_arch_support,
                'is_calculated': True,
            })
        
        # Purlin components
        big_arch_purlin = self.no_of_bays * self.no_of_spans
        if big_arch_purlin > 0:
            component_vals.append({
                'project_id': self.id,
                'section': 'truss',
                'name': 'Big Arch Purlin',
                'nos': big_arch_purlin,
                'length': self.bay_width,
                'is_calculated': True,
            })
        
        small_arch_purlin = big_arch_purlin
        if small_arch_purlin > 0:
            component_vals.append({
                'project_id': self.id,
                'section': 'truss',
                'name': 'Small Arch Purlin',
                'nos': small_arch_purlin,
                'length': self.bay_width,
                'is_calculated': True,
            })
        
        gable_purlin = 0 if self.last_span_gutter else self.no_of_bays * 2
        if gable_purlin > 0:
            component_vals.append({
                'project_id': self.id,
                'section': 'truss',
                'name': 'Gable Purlin',
                'nos': gable_purlin,
                'length': self.bay_width,
                'is_calculated': True,
            })
        
        # Border Purlins
        bay_border = int(self.bay_side_border_purlin) * self.no_of_bays * 2
        if bay_border > 0:
            component_vals.append({
                'project_id': self.id,
                'section': 'truss',
                'name': 'Bay Side Border Purlin',
                'nos': bay_border,
                'length': self.bay_width,
                'is_calculated': True,
            })
        
        span_border = int(self.span_side_border_purlin) * self.no_of_spans * (int(self.no_column_big_frame) + 1) * 2
        if span_border > 0:
            span_side_length = self.span_width / (int(self.no_column_big_frame) + 1)
            component_vals.append({
                'project_id': self.id,
                'section': 'truss',
                'name': 'Span Side Border Purlin',
                'nos': span_border,
                'length': span_side_length,
                'is_calculated': True,
            })
        
        # Create all component records
        for val in component_vals:
            try:
                self.env['greenhouse.component.line'].create(val)
                _logger.info(f"Created truss component: {val['name']} - Nos: {val['nos']}")
            except Exception as e:
                _logger.error(f"Error creating truss component {val.get('name', 'Unknown')}: {e}")