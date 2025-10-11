from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class GreenMasterLower(models.Model):
    _inherit = 'green.master'
    
    # Cross Bracing Configuration
    front_back_c_c_cross_bracing_x = fields.Boolean('Front & Back Column to Column Cross bracing X', 
                                                   default=False, tracking=True)
    middle_c_c_cross_bracing_x = fields.Integer('No of Internal Column lines for Column to Column Cross Bracing X', 
                                               default=0, tracking=True)
    cross_bracing_column_arch = fields.Boolean('Cross Bracing Column to Arch', default=False, tracking=True)
    cross_bracing_column_bottom = fields.Boolean('Cross Bracing Column to Bottom Chord', default=False, tracking=True)
    
    # Arch Middle Purlin Configuration
    arch_middle_purlin_big_arch = fields.Selection([
        ('0', '0'),
        ('1','4 Corners'),
        ('2','Front & Back'),
        ('3','Both Sides'),
        ('4','4 Sides'),
        ('5','All')
    ], string='Arch Middle Purlin Big Arch', required=True, default='0', tracking=True)
    
    arch_middle_purlin_big_arch_pcs = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2')
    ], string='Arch Middle Purlin Big Arch Pcs', required=True, default='0', tracking=True)
    
    arch_middle_purlin_small_arch = fields.Selection([
        ('0', '0'),
        ('1','4 Corners'),
        ('2','Front & Back'),
        ('3','Both Sides'),
        ('4','4 Side'),
        ('5','All')
    ], string='Arch Middle Purlin Small Arch', required=True, default='0', tracking=True)
    
    arch_middle_purlin_small_arch_pcs = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2')
    ], string='Arch Middle Purlin Small Arch Pcs', required=True, default='0', tracking=True)
    
    # Gutter Configuration
    gutter_type = fields.Selection([
        ('none', 'None'),
        ('ippf', 'IPPF'),
        ('continuous', 'Continuous'),
    ], string='Gutter', default='none', required=True, tracking=True)
    
    gutter_ippf_full = fields.Boolean('Gutter IPPF Full', default=False, tracking=True)
    gutter_ippf_drainage_extension = fields.Boolean('Gutter IPPF Drainage Extension', default=False, tracking=True)
    gutter_funnel_ippf = fields.Boolean('Gutter Funnel IPPF', default=False, tracking=True)
    gutter_end_cap = fields.Boolean('Gutter End Cap', default=False, tracking=True)
    
    gutter_extension = fields.Selection([
        ('0', '0'),
        ('2', '2'),
        ('4', '4'),
    ], string='Gutter Extension', default='0', tracking=True)
    
    # Length Master Fields for Lower Section
    length_front_back_c_c_cross_bracing_x = fields.Many2one(
        'length.master', 
        string='Length for Front Back Column to Column Cross Bracing X',
        domain="[('available_for_fields.name', '=', 'length_front_back_c_c_cross_bracing_x'), ('active', '=', True)]",
        tracking=True
    )
    
    length_middle_c_c_cross_bracing_x = fields.Many2one(
        'length.master', 
        string='Length for Internal CC Cross Bracing X',
        domain="[('available_for_fields.name', '=', 'length_middle_c_c_cross_bracing_x'), ('active', '=', True)]",
        tracking=True
    )
    
    length_cross_bracing_column_arch = fields.Many2one(
        'length.master', 
        string='Length for Cross Bracing Column Arch',
        domain="[('available_for_fields.name', '=', 'length_cross_bracing_column_arch'), ('active', '=', True)]",
        tracking=True
    )
    
    length_cross_bracing_column_bottom = fields.Many2one(
        'length.master', 
        string='Length for Cross Bracing Column Bottom',
        domain="[('available_for_fields.name', '=', 'length_cross_bracing_column_bottom'), ('active', '=', True)]",
        tracking=True
    )
    
    @api.onchange('gutter_type')
    def _onchange_gutter_type(self):
        if self.gutter_type == 'none':
            self.gutter_ippf_full = False
            self.gutter_ippf_drainage_extension = False
            self.gutter_funnel_ippf = False
            self.gutter_end_cap = False
            self.gutter_extension = '0'
        elif self.gutter_type == 'ippf':
            self.gutter_extension = '0'
        elif self.gutter_type == 'continuous':
            self.gutter_ippf_full = False
            self.gutter_ippf_drainage_extension = False
            self.gutter_funnel_ippf = False
            self.gutter_end_cap = False
    
    def _calculate_all_components(self):
        """Extend calculation to add lower section components"""
        super()._calculate_all_components()
        self._calculate_lower_components()
    
    def _calculate_lower_components(self):
        """Calculate lower section-specific components"""
        component_vals = []
        
        # Cross Bracing calculations
        no_front_back_c_c_cross_bracing_x = int(self.front_back_c_c_cross_bracing_x) * (self.no_of_spans + 1) * 4
        no_middle_c_c_cross_bracing_x = self.middle_c_c_cross_bracing_x * (self.no_of_spans + 1) * 2
        no_cross_bracing_column_arch = int(self.cross_bracing_column_arch) * (self.no_of_spans * 4)
        no_cross_bracing_column_bottom = int(self.cross_bracing_column_bottom) * (self.no_of_spans * 4)
        
        # Arch Middle Purlin calculations
        no_arch_middle_purlin_small_arch = 0
        if self.arch_middle_purlin_small_arch == '0':
            no_arch_middle_purlin_small_arch = 0
        elif self.arch_middle_purlin_small_arch == '1':
            no_arch_middle_purlin_small_arch = int(self.arch_middle_purlin_small_arch_pcs) * 4
        elif self.arch_middle_purlin_small_arch == '2':
            no_arch_middle_purlin_small_arch = int(self.arch_middle_purlin_small_arch_pcs) * (self.no_of_spans * 2)
        elif self.arch_middle_purlin_small_arch == '3':
            no_arch_middle_purlin_small_arch = int(self.arch_middle_purlin_small_arch_pcs) * (self.no_of_bays * 2)
        elif self.arch_middle_purlin_small_arch == '4':
            no_arch_middle_purlin_small_arch = int(self.arch_middle_purlin_small_arch_pcs) * ((self.no_of_spans * 2) + (self.no_of_bays * 2) - 4)
        elif self.arch_middle_purlin_small_arch == '5':
            no_arch_middle_purlin_small_arch = int(self.arch_middle_purlin_small_arch_pcs) * (self.no_of_spans * self.no_of_bays)
        
        no_arch_middle_purlin_big_arch = 0
        if self.arch_middle_purlin_big_arch == '0':
            no_arch_middle_purlin_big_arch = 0
        elif self.arch_middle_purlin_big_arch == '1':
            no_arch_middle_purlin_big_arch = int(self.arch_middle_purlin_big_arch_pcs) * 4
        elif self.arch_middle_purlin_big_arch == '2':
            no_arch_middle_purlin_big_arch = int(self.arch_middle_purlin_big_arch_pcs) * (self.no_of_spans * 2)
        elif self.arch_middle_purlin_big_arch == '3':
            no_arch_middle_purlin_big_arch = int(self.arch_middle_purlin_big_arch_pcs) * (self.no_of_bays * 2)
        elif self.arch_middle_purlin_big_arch == '4':
            no_arch_middle_purlin_big_arch = int(self.arch_middle_purlin_big_arch_pcs) * ((self.no_of_spans * 2) + (self.no_of_bays * 2) - 4)
        elif self.arch_middle_purlin_big_arch == '5':
            no_arch_middle_purlin_big_arch = int(self.arch_middle_purlin_big_arch_pcs) * (self.no_of_spans * self.no_of_bays)
        
        # Gutter calculations
        no_gutter_ippf_full = 0
        no_gutter_ippf_drainage_ext = 0
        no_gutter_funnel_ippf_funnel = 0
        no_gutter_end_cap = 0
        
        no_gutters_continuous = 0
        gutter_length_continuous = 0
        gutter_purlin_length_continuous = 0
        gutter_purlin_nos_continuous = 0
        gutter_purlin_extension_nos = 0
        gutter_purlin_extension_length = 0
        
        if self.gutter_type == 'ippf':
            if self.gutter_ippf_full:
                if self.last_span_gutter:
                    no_gutter_ippf_full = (self.no_of_spans + 1) * self.no_of_bays
                else:
                    no_gutter_ippf_full = (self.no_of_spans - 1) * self.no_of_bays
            
            if self.gutter_ippf_drainage_extension:
                if self.last_span_gutter:
                    no_gutter_ippf_drainage_ext = (self.no_of_spans + 1) * int(self.gutter_slope)
                else:
                    no_gutter_ippf_drainage_ext = (self.no_of_spans - 1) * int(self.gutter_slope)
            
            if self.gutter_funnel_ippf:
                if self.last_span_gutter:
                    no_gutter_funnel_ippf_funnel = (self.no_of_spans + 1) * int(self.gutter_slope)
                else:
                    no_gutter_funnel_ippf_funnel = (self.no_of_spans - 1) * int(self.gutter_slope)
            
            if self.gutter_end_cap and self.gutter_funnel_ippf and int(self.gutter_slope) == 1:
                if self.last_span_gutter:
                    no_gutter_end_cap = self.no_of_spans + 1
                else:
                    no_gutter_end_cap = self.no_of_spans - 1
        
        elif self.gutter_type == 'continuous':
            no_gutters_continuous = self.no_of_spans - 1
            gutter_length_continuous = self.span_length + int(self.gutter_extension)
            gutter_purlin_length_continuous = self.bay_width
            gutter_purlin_nos_continuous = (self.no_of_spans - 1) * self.no_of_bays * 2
            gutter_purlin_extension_nos = (self.no_of_spans - 1) * 4
            gutter_purlin_extension_length = int(self.gutter_extension)
        
        # Create Cross Bracing components
        if no_front_back_c_c_cross_bracing_x > 0:
            front_back_bracing_length = self._get_length_master_value(self.length_front_back_c_c_cross_bracing_x, 2.5)
            component_vals.append(self._create_component_val(
                'lower', 'Front & Back Column to Column Cross Bracing X', 
                no_front_back_c_c_cross_bracing_x, 
                front_back_bracing_length,
                self.length_front_back_c_c_cross_bracing_x
            ))
        
        if no_middle_c_c_cross_bracing_x > 0:
            middle_bracing_length = self._get_length_master_value(self.length_middle_c_c_cross_bracing_x, 2.5)
            component_vals.append(self._create_component_val(
                'lower', 'Internal CC Cross Bracing X', 
                no_middle_c_c_cross_bracing_x, 
                middle_bracing_length,
                self.length_middle_c_c_cross_bracing_x
            ))
        
        if no_cross_bracing_column_arch > 0:
            column_arch_bracing_length = self._get_length_master_value(self.length_cross_bracing_column_arch, 2.0)
            component_vals.append(self._create_component_val(
                'lower', 'Cross Bracing Column to Arch', 
                no_cross_bracing_column_arch, 
                column_arch_bracing_length,
                self.length_cross_bracing_column_arch
            ))
        
        if no_cross_bracing_column_bottom > 0:
            column_bottom_bracing_length = self._get_length_master_value(self.length_cross_bracing_column_bottom, 2.0)
            component_vals.append(self._create_component_val(
                'lower', 'Cross Bracing Column to Bottom Chord', 
                no_cross_bracing_column_bottom, 
                column_bottom_bracing_length,
                self.length_cross_bracing_column_bottom
            ))
        
        # Create Arch Middle Purlin components
        if no_arch_middle_purlin_big_arch > 0:
            component_vals.append(self._create_component_val(
                'lower', 'Arch Middle Purlin Big Arch', 
                no_arch_middle_purlin_big_arch, 
                self.bay_width
            ))
        
        if no_arch_middle_purlin_small_arch > 0:
            component_vals.append(self._create_component_val(
                'lower', 'Arch Middle Purlin Small Arch', 
                no_arch_middle_purlin_small_arch, 
                self.bay_width
            ))
        
        # Create Gutter components
        if no_gutter_ippf_full > 0:
            component_vals.append(self._create_component_val(
                'lower', 'Gutter IPPF Full', 
                no_gutter_ippf_full, 
                self.bay_width + 0.04
            ))
        
        if no_gutter_funnel_ippf_funnel > 0:
            component_vals.append(self._create_component_val(
                'lower', 'Gutter Funnel IPPF', 
                no_gutter_funnel_ippf_funnel, 
                0.5
            ))
        
        if no_gutter_ippf_drainage_ext > 0:
            component_vals.append(self._create_component_val(
                'lower', 'Gutter IPPF Drainage Extension', 
                no_gutter_ippf_drainage_ext, 
                0.3
            ))
        
        if no_gutter_end_cap > 0:
            component_vals.append(self._create_component_val(
                'lower', 'Gutter End Cap', 
                no_gutter_end_cap, 
                0.1
            ))
        
        if no_gutters_continuous > 0:
            component_vals.append(self._create_component_val(
                'lower', 'Gutter Continuous', 
                no_gutters_continuous, 
                gutter_length_continuous
            ))
        
        if gutter_purlin_nos_continuous > 0:
            component_vals.append(self._create_component_val(
                'lower', 'Gutter Purlin', 
                gutter_purlin_nos_continuous, 
                gutter_purlin_length_continuous
            ))
        
        if gutter_purlin_extension_nos > 0 and gutter_purlin_extension_length > 0:
            component_vals.append(self._create_component_val(
                'lower', 'Gutter Purlin For Extension', 
                gutter_purlin_extension_nos, 
                gutter_purlin_extension_length
            ))
        
        # Create all lower component lines
        for val in component_vals:
            try:
                self.env['component.line'].create(val)
                _logger.info(f"Created lower component: {val['name']} - Nos: {val['nos']} - Length: {val['length']}")
            except Exception as e:
                _logger.error(f"Error creating lower component {val.get('name', 'Unknown')}: {e}")