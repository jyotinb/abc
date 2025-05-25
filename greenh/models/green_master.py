from odoo import _,models, fields, api
from odoo.exceptions import ValidationError
from math import ceil,sqrt 

class LengthMaster(models.Model):
    _name = 'length.master'
    _description = 'Lengths'
    _order = 'length_value asc'
        
    length_value = fields.Float(string='Length Value', required=True)
    available_for_fields = fields.Many2many(
        'ir.model.fields',
        string='Available For Fields',
        domain="[('model', '=', 'green.master')]"
    )
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('length_value')
    def _compute_display_name(self):
        for record in self:
            # Only display the length_value in dropdowns
            record.display_name = str(record.length_value)
    
class GreenMaster(models.Model):
    _name = 'green.master'
    _description = 'Greenhouse Master'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Inherit from mail.thread to enable messaging

    id = fields.Integer('ID', required=True)
    customer = fields.Char('Customer', size=50)
    address = fields.Char('Address', size=200)
    city = fields.Char('City', size=50)
    mobile = fields.Char('Mobile', size=13)
    email = fields.Char('Email', size=40)
    reference = fields.Char('Reference', size=300)
    structure_type = fields.Selection([
        ('NVPH', 'NVPH'),
        ('NVPH2', 'NVPH2'),
    ], string='Structure Type', required=True, default='NVPH')
    plot_size = fields.Char('Plot Size', size=20)
    total_span_length = fields.Float('Total Span Length')
    total_bay_length = fields.Float('Total Bay Length')
    span_length = fields.Float('Span Length', default=0.00)
    bay_length = fields.Float('Bay Length', default=0.00)
    structure_size = fields.Float('Structure Size', default=0.00)
    gutter_length = fields.Float('Gutter Length', default=0.00)
    span_width = fields.Float('Span Width', default=0.00)
    bay_width = fields.Float('Bay Width', default=0.00)
    no_of_bays = fields.Integer('Number of Bays', default=0)
    no_of_spans = fields.Integer('Number of Spans', default=0)
    gutter_slope = fields.Selection([
        ('1', '1'),('2', '2')],string = 'Gutter Slope', default='1')
    last_span_gutter = fields.Boolean('Last Span Gutter', default=False)
    last_span_gutter_length = fields.Integer('Last Span Gutter Length', default=0)
    top_ridge_height = fields.Float('Top Ridge Height', default=0.00)
    column_height = fields.Float('Column Height', default=0.00)
    bottom_height = fields.Float('Bottom Height', default=0.00)
    foundation_length = fields.Float('Foundation Length', default=0.00)
    arch_height = fields.Float('Arch Height', default=0.00)
    big_arch_length = fields.Float('Big Arch Length', default=0.00)
    small_arch_length = fields.Float('Small Arch Length', default=0.00)
    bottom_chord_af_normal = fields.Integer('Bottom Chord Anchor Frame Singular', default=0)
    bottom_chord_af_normal_pipe_id = fields.Many2one('pipe.management', string='Bottom Chord Anchor Frame Singular Pipe', required=False) 
    bottom_chord_af_male = fields.Integer('Bottom Chord Anchor Frame Male', default=0)
    bottom_chord_af_male_pipe_id = fields.Many2one('pipe.management', string='Bottom Chord Anchor Frame Male Pipe', required=False)
    bottom_chord_af_female = fields.Integer('Bottom Chord Anchor Frame Female', default=0)
    bottom_chord_af_female_pipe_id = fields.Many2one('pipe.management', string='Bottom Chord Anchor Frame Female Pipe', required=False)
    bottom_chord_il_normal = fields.Integer('Bottom Chord Inner Line Singular', default=0)
    bottom_chord_il_normal_pipe_id = fields.Many2one('pipe.management', string='Bottom Chord Inner Line Singular Pipe', required=False) 
    bottom_chord_il_male = fields.Integer('Bottom Chord Inner Line Male', default=0)
    bottom_chord_il_male_pipe_id = fields.Many2one('pipe.management', string='Bottom Chord Inner Line Male Pipe', required=False) 
    bottom_chord_il_female = fields.Integer('Bottom Chord Inner Line Female', default=0)
    bottom_chord_il_female_pipe_id = fields.Many2one('pipe.management', string='Bottom Chord Inner Line Female Pipe', required=False) 
    is_bottom_chord = fields.Boolean('Is Bottom Chord Required ?', default=False)
    v_support_bottom_chord_frame = fields.Selection([
        ('0', '0'),('2', '2')],'V Support Bottom Chord per Frame', default='0')
    no_v_support_bottom_chord = fields.Integer('Number of V Support Bottom Chord', default=0)
    v_support_bottom_chord_pipe_id = fields.Many2one('pipe.management', string='V Support Bottom Chord Pipe', required=False) 
    arch_big = fields.Integer('Big Arch', default=0)
    arch_big_pipe_id = fields.Many2one('pipe.management', string='Big Arch Pipe', required=False)
    arch_small = fields.Integer('Small Arch', default=0)
    arch_small_pipe_id = fields.Many2one('pipe.management', string='Small Arch Pipe', required=False)
    
    
    arch_support_staraight_middle = fields.Integer('Arch Support Straight Middle', default=0)
    arch_support_staraight_middle_pipe_id = fields.Many2one('pipe.management', string='Arch Support Straight Middle Pipe', required=False)
    is_arch_support_big = fields.Boolean('Is Arch Support Big (Both Arches) Required ?', default=False)
    is_arch_support_small_big_arch = fields.Boolean('Is Arch Support Small for Bigger Arch Required?', default=False)
    is_arch_support_small_small_arch = fields.Boolean('Is Arch Support Small for Smaller Arch Required?', default=False)
    arch_support_big = fields.Integer('Arch Support Big (Both Arches) ', default=0)
    arch_support_big_pipe_id = fields.Many2one('pipe.management', string='Arch Support Big (Both Arches) Pipe', required=False)
    arch_support_small_big_arch = fields.Integer('Arch Support Small for Big Arch', default=0)
    arch_support_small_big_arch_pipe_id = fields.Many2one('pipe.management', string='Arch Support Small for Big Arch Pipe', required=False)
    arch_support_small_small_arch = fields.Integer('Arch Support Small for Small Arch', default=0)
    arch_support_small_small_arch_pipe_id = fields.Many2one('pipe.management', string='Arch Support Small for Small Arch Pipe', required=False)
    vent_big_arch_support = fields.Integer('Vent Big Arch Support', default=0)
    vent_big_arch_support_pipe_id = fields.Many2one('pipe.management', string='Vent Big Arch Support Pipe', required=False)
    vent_small_arch_support = fields.Integer('Vent Small Arch Support', default=0)
    vent_small_arch_support_pipe_id = fields.Many2one('pipe.management', string='Vent Small Arch Support Pipe', required=False)
    
    big_arch_purlin = fields.Integer('Big Arch Purlin', default=0)
    big_arch_purlin_pipe_id = fields.Many2one('pipe.management', string='Big Arch Purlin Pipe', required=False)
    small_arch_purlin = fields.Integer('Small Arch Purlin', default=0)
    small_arch_purlin_pipe_id = fields.Many2one('pipe.management', string='Small Arch Purlin Pipe', required=False)
    gable_purlin = fields.Integer('Gable Purlin', default=0)
    gable_purlin_pipe_id = fields.Many2one('pipe.management', string='Gable Purlin Pipe', required=False)
    bay_side_border_purlin = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2')], string='Bay Side Border Purlin', required=True, default='0')
    span_side_border_purlin = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2')], string='Span Side Border Purlin', required=True, default='0')
    no_bay_side_border_purlin = fields.Integer('Number of Bay Side Border Purlin', default=0)
    bay_side_border_purlin_pipe_id = fields.Many2one('pipe.management', string='Bay Side Border Purlin Pipe', required=False)
    no_span_side_border_purlin = fields.Integer('Number of Span Side Border Purlin', default=0)
    span_side_border_purlin_pipe_id = fields.Many2one('pipe.management', string='Span Side Border Purlin Pipe', required=False)
    
    
    
    no_vent_big_arch_support_frame = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2'),('3', '3')], string='Vent Support for Big Arch per Frame', required=True, default='0')
    no_vent_small_arch_support_frame = fields.Selection([
        ('0', '0'),('2', '2')], string='Vent Support for Small Arch per Frame', required=True, default='0')
    no_column_big_frame = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2'),('3', '3')
    ], string='No of Big Column per Anchor Frame', required=True, default='0')
    no_anchor_frame_lines = fields.Integer('Number of Anchor Frame Lines', default=0)
    total_anchor_frames = fields.Integer('Total Anchor Frames', default=0)
    no_middle_columns = fields.Integer('Number of Middle Columns', default=0)
    pipe_id = fields.Many2one('pipe.management', string='Middle Columns Pipe', required=False)
    middle_column_pipe_id = fields.Many2one('pipe.management', string='Middle Column Pipe', required=False)
    no_quadraple_columns = fields.Integer('Number of Quadruple Columns', default=0)
    quadraple_columns_pipe_id = fields.Many2one('pipe.management', string='Quadruple Column Pipe', required=False)
    no_main_columns = fields.Integer('Number of Main Columns', default=0)
    main_columns_pipe_id = fields.Many2one('pipe.management', string='Main Column Pipe', required=False)
    total_normal_frames = fields.Integer('Total Normal Frames', default=0)
    thick_column = fields.Selection([
        ('0', '0'),( '1','4 Corners'),( '2','Both Bay Side'),( '3','Both Span Side'),( '4','All 4 Side')
    ], string='Thick Column Option', required=True, default='0')
    no_thick_columns = fields.Integer('Number of Thick Columns', default=0)
    thick_column_pipe_id = fields.Many2one('pipe.management', string='Thick Column Pipe', required=False)
    
    side_screen_roll_up_pipe = fields.Integer('Number of Side Screen Roll Up Pipe', default=0)
    side_screen_roll_up_pipe_pipe_id = fields.Many2one('pipe.management', string='Side Screen Roll Up Pipe', required=False)
    side_screen_roll_up_pipe_joiner = fields.Integer('Side Screen Roll Up Pipe Joiner', default=0)
    side_screen_roll_up_pipe_joiner_pipe_id = fields.Many2one('pipe.management', string='Side Screen Roll Up Pipe Joiner Pipe', required=False)
    side_screen_guard = fields.Boolean('Side Screen Guard', default=False)
    side_screen_guard_pipe_id = fields.Many2one('pipe.management', string='Side Screen Guard Pipe', required=False)
    no_side_screen_guard = fields.Integer('Number of Side Screen Guard', default=0)
    side_screen_guard_box = fields.Boolean('Side Screen Guard Box', default=False)
    
    no_side_screen_guard_box = fields.Integer('Number of Side Screen Guard Box', default=0)
    no_side_screen_guard_box_pipe = fields.Integer('Number of Side Screen Guard Box Pipe', default=0)
    side_screen_guard_box_pipe_id = fields.Many2one('pipe.management', string='Side Screen Guard Box Pipe', required=False)
    no_side_screen_guard_box_h_pipe = fields.Integer('Number of Side Screen Guard Box H Pipe', default=0)
    side_screen_guard_box_h_pipe_pipe_id = fields.Many2one('pipe.management', string='Side Screen Guard Box H Pipe', required=False)
    front_back_c_c_cross_bracing_x = fields.Boolean('Front & Back Column to Column Cross bracing X', default=False)
    front_back_c_c_cross_bracing_x_pipe_id = fields.Many2one('pipe.management', string='Front & Back Column to Column Cross bracing X Pipe', required=False)
    no_front_back_c_c_cross_bracing_x = fields.Integer('No of Front Back Column to Column Cross Bracing X*', default=0)
    middle_c_c_cross_bracing_x = fields.Integer('No of Internal Column lines for Column to Column Cross Bracing X', default=0)
    middle_c_c_cross_bracing_x_pipe_id = fields.Many2one('pipe.management', string='Internal Column lines for Column to Column Cross Bracing X Pipe', required=False)
    no_middle_c_c_cross_bracing_x = fields.Integer('Number of Internal CC Cross Bracing X', default=0)
    cross_bracing_column_arch = fields.Boolean('Cross Bracing Column to Arch', default=0)
    cross_bracing_column_arch_pipe_id = fields.Many2one('pipe.management', string='Cross Bracing Column to Arch Pipe', required=False)
    no_cross_bracing_column_arch = fields.Integer('Number of Cross Bracing Column Arch', default=0)
    cross_bracing_column_bottom = fields.Boolean('Cross Bracing Column to Bottom Chord', default=False)
    cross_bracing_column_bottom_pipe_id = fields.Many2one('pipe.management', string='Cross Bracing Column to Bottom Chord Pipe', required=False)
    no_cross_bracing_column_bottom = fields.Integer('Number of Cross Bracing Column Bottom', default=0)
    arch_middle_purlin_big_arch = fields.Selection([
        ('0', '0'),( '1','4 Corners'),( '2','Front & Back'),( '3','Both Sides'),( '4','All 4 Side'),( '5','4 Sides'),( '6','All')], string='Arch Middle Purlin Big Arch', required=True, default='0')
    arch_middle_purlin_big_arch_pipe_id = fields.Many2one('pipe.management', string='Arch Middle Purlin Big Arch Pipe', required=False)    
    arch_middle_purlin_big_arch_pcs = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2')], string='Arch Middle Purlin Big Arch Pcs', required=True, default=0)
    no_arch_middle_purlin_big_arch = fields.Integer('Number of Arch Middle Purlin Big Arch', default=0)
    arch_middle_purlin_small_arch = fields.Selection([
        ('0', '0'),( '1','4 Corners'),( '2','Front & Back'),( '3','Both Sides'),( '4','All 4 Side'),( '5','4 Sides'),( '6','All')], string='Arch Middle Purlin Small Arch', required=True, default='0')
    arch_middle_purlin_small_arch_pipe_id = fields.Many2one('pipe.management', string='Arch Middle Purlin Small Arch Pipe', required=False)
    arch_middle_purlin_small_arch_pcs = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2')], string='Arch Middle Purlin Small Arch Pcs', required=True, default=0)
    no_arch_middle_purlin_small_arch = fields.Integer('Number of Arch Middle Purlin Small Arch', default=0)
    side_screen_guard_spacer = fields.Integer('Side Screen Guard Spacer', default='0')
    
    side_screen_guard_spacer_pipe_id = fields.Many2one('pipe.management', string='Side Screen Guard Space Pipe', required=False)
    side_screen_roll_up_handle = fields.Integer('Side Screen Roll Up Handle', default='0')
    gutter_ippf_full = fields.Boolean('Gutter IPPF Full', default=False)
    no_gutter_ippf_drainage_ext = fields.Integer('Number of Gutter IPPF Drainage Extension', default=0)
    gutter_ippf_drainage_extension = fields.Boolean('Gutter IPPF Drainage Extension', default=False)
    gutter_funnel_ippf = fields.Boolean('Gutter Funnel IPPF', default=False)
    no_gutter_ippf_full = fields.Integer('Number of Gutter IPPF Full', default=0)
    gutter_end_cap = fields.Boolean('Gutter End Cap', default=False)
    no_gutter_slopes = fields.Integer('Number of Gutter Slopes', default=0)
    no_gutter_funnel_ippf_funnel = fields.Integer('Number of Gutter Funnel IPPF Funnel', default=0)
    no_gutter_end_cap = fields.Integer('Number of Gutter End Cap', default=0)
    is_side_coridoors = fields.Boolean('Is ASC', default=False)
    width_front_span_coridoor = fields.Float('Width Front Span ASC', default=0.00)
    width_back_span_coridoor = fields.Float('Width Back Span ASC', default=0.00)
    width_front_bay_coridoor = fields.Float('Width Left Bay ASC', default=0.00)
    width_back_bay_coridoor = fields.Float('Width Right Bay ASC', default=0.00)
    length_front_span_coridoor = fields.Float('Length Front Span ASC', default=0.00)
    length_back_span_coridoor = fields.Float('Length Back Span ASC', default=0.00)
    length_front_bay_coridoor = fields.Float('Length Left Bay ASC', default=0.00)
    length_back_bay_coridoor = fields.Float('Length Right Bay ASC', default=0.00)
    support_hockeys = fields.Integer('Support per Hockey', default=False)
    no_hockey_support = fields.Integer('Number of Hockey Support', default=0)
    hockey_support_pipe_id = fields.Many2one('pipe.management', string='Hockey Support Pipe', required=False)

    no_front_span_coridoor_hockeys = fields.Integer('Number of Front Span ASC Pipe', default=0)
    front_span_coridoor_hockeys_pipe_id = fields.Many2one('pipe.management', string='Front Span ASC Pipe', required=False)
    no_back_span_coridoor_hockeys = fields.Integer('Number of Back Span ASC Pipe', default=0)
    back_span_coridoor_hockeys_pipe_id = fields.Many2one('pipe.management', string='Back Span ASC Pipe', required=False)
    no_front_bay_coridoor_hockeys = fields.Integer('Number of Left Bay ASC Pipe', default=0)
    front_bay_coridoor_hockeys_pipe_id = fields.Many2one('pipe.management', string='Left Bay ASC Pipe', required=False)
    no_back_bay_coridoor_hockeys = fields.Integer('Number of Right Bay ASC Pipe', default=0)
    back_bay_coridoor_hockeys_pipe_id = fields.Many2one('pipe.management', string='Right Bay ASC Pipe', required=False)
    no_total_hockeys = fields.Integer('Total Number of Hockeys', default=0)
    no_asc = fields.Integer('Total ASC', default=0)
    length_middle_column = fields.Float('Length of Middle Column', default = 0.00)
    length_quadraple_column = fields.Float('Length of Quadruple Column', default = 0.00)
    length_main_column = fields.Float('Length of Main Column', default = 0.00)
    length_thick_column = fields.Float('Length of Thick Column', default = 0.00)
    length_front_span_coridoor_hockey = fields.Float('Length of Front Span ASC Pipe', default = 0.00)
    length_back_span_coridoor_hockey = fields.Float('Length of Back Span ASC Pipe', default = 0.00)
    length_front_bay_coridoor_hockey = fields.Float('Length of Left Bay ASC Pipe', default = 0.00)
    length_back_bay_coridoor_hockey = fields.Float('Length of Right Bay ASC Pipe', default = 0.00)
    length_support_hockeys = fields.Many2one(
        'length.master', string='Length for Support Hockey', 
        domain="[('available_for_fields.name', '=', 'length_support_hockeys')]"
    )
    
    
    
    length_bottom_chord_af_normal = fields.Float('Length of Bottom Chord Anchor Frame Singular', default = 0.00)
    length_bottom_chord_af_male =  fields.Float('Length of Bottom Chord Anchor Frame Male', default = 0.00)
    length_bottom_chord_af_female =  fields.Float('Length of Bottom Chord Anchor Frame Female', default = 0.00)
    length_bottom_chord_il_normal = fields.Float('Length of Bottom Chord Inner Frame Singular', default = 0.00)
    length_bottom_chord_il_male =  fields.Float('Length of Bottom Chord Inner Frame Male', default = 0.00)
    length_bottom_chord_il_female =  fields.Float('Length of Bottom Chord Inner Frame Female', default = 0.00)
    #length_v_support_bottom_chord_frame =  fields.Float('Length of V Support Bottom Chord', default = 0.00) 
    #length_arch_support_big =  fields.Float('Length of Arch Support Big (Both Arches)', default = 0.00)
    #length_arch_support_small_big_arch  =  fields.Float('Length of Arch Support Small for Bigger Arch', default = 0.00)
    
    length_arch_support_staraight_middle  =  fields.Float('Length of Arch Support Straight Middle', default = 0.00) 
    
    
    
    
    length_v_support_bottom_chord_frame = fields.Many2one(
        'length.master', string='Length for V Support Bottom Chord ', 
        domain="[('available_for_fields.name', '=', 'length_v_support_bottom_chord_frame')]"
    )

    length_arch_support_big = fields.Many2one(
        'length.master', string='Length for Arch Support Big', 
        domain="[('available_for_fields.name', '=', 'length_arch_support_big')]"
    )
    
    length_arch_support_small_big_arch = fields.Many2one(
        'length.master', string='Length for Arch Support Small for Big Arch', 
        domain="[('available_for_fields.name', '=', 'length_arch_support_small_big_arch')]"
    )
    
    
    length_arch_support_small_small_arch = fields.Many2one(
        'length.master', string='Length for Arch Support Small for Small Arch', 
        domain="[('available_for_fields.name', '=', 'length_arch_support_small_small_arch')]"
    )
    
    length_vent_big_arch_support = fields.Many2one(
        'length.master', string='Length for Vent Support for Big Arch', 
        domain="[('available_for_fields.name', '=', 'length_vent_big_arch_support')]"
    )
    
    
    length_vent_small_arch_support = fields.Many2one(
        'length.master', string='Length for Vent Support for Small Arch', 
        domain="[('available_for_fields.name', '=', 'length_vent_small_arch_support')]"
    )
    
    length_big_arch_purlin = fields.Float('Length of Big Arch Purlin', default = 0.00) 
    length_small_arch_purlin = fields.Float('Length of Small Arch Purlin', default = 0.00) 
    length_gable_purlin = fields.Float('Length of Gable Purlin', default = 0.00) 
    length_bay_side_border_purlin = fields.Float('Length of Bay Side Border Purlin', default = 0.00) 
    length_span_side_border_purlin = fields.Float('Length of Span Side Border Purlin', default = 0.00)
    length_side_screen_roll_up_pipe = fields.Float('Length of Side Screen Roll up Pipe', default = 0.00)
    length_side_screen_roll_up_pipe_joiner = fields.Many2one(
        'length.master', string='Length for Side Screen Roll Up Pipe Joiner', 
        domain="[('available_for_fields.name', '=', 'length_side_screen_roll_up_pipe_joiner')]"
    )
    length_side_screen_guard = fields.Many2one(
        'length.master', string='Length for Side Screen Guard', 
        domain="[('available_for_fields.name', '=', 'length_side_screen_guard')]"
    )
    
    length_front_back_c_c_cross_bracing_x = fields.Many2one(
        'length.master', string='Length for Front Back Column to Column Cross Bracing X', 
        domain="[('available_for_fields.name', '=', 'length_front_back_c_c_cross_bracing_x')]"
    )
    length_middle_c_c_cross_bracing_x = fields.Many2one(
        'length.master', string='Length for Internal CC Cross Bracing X', 
        domain="[('available_for_fields.name', '=', 'length_middle_c_c_cross_bracing_x')]"
    )
    length_cross_bracing_column_arch = fields.Many2one(
        'length.master', string='Length for Cross Bracing Column Arch', 
        domain="[('available_for_fields.name', '=', 'length_cross_bracing_column_arch')]"
    )
    length_cross_bracing_column_bottom = fields.Many2one(
        'length.master', string='Length for Cross Bracing Column Bottom', 
        domain="[('available_for_fields.name', '=', 'length_cross_bracing_column_bottom')]"
    )
    length_arch_middle_purlin_big_arch = fields.Float('Length of Arch Middle Purlin Big Arch', default = 0.00)
    length_arch_middle_purlin_small_arch = fields.Float('Length of Arch Middle Purlin Small Arch', default = 0.00)
    length_side_screen_guard_spacer = fields.Many2one(
        'length.master', string='Length for Side Screen Guard Spacer', 
        domain="[('available_for_fields.name', '=', 'length_side_screen_guard_spacer')]"
    )
    length_gutter_ippf_full = fields.Float('Length of Gutter IPPF Full', default = 0.00)
    length_side_screen_guard_box_pipe = fields.Float('Length for Side Screen Guard Box Pipe', default = 0.00)
    length_side_screen_guard_box_h_pipe = fields.Many2one(
        'length.master', string='Length for Side Screen Guard Box H Pipe', 
        domain="[('available_for_fields.name', '=', 'length_side_screen_guard_box_h_pipe')]"
    )
     
    # @api.onchange('is_bottom_chord')
    # def _onchange_is_bottom_chord(self):
        # for record in self:
            # if not record.is_bottom_chord:
                # record.v_support_bottom_chord_frame = '0'
                # #record.bottom_chord_af_normal = 0
                # record.bottom_chord_af_male = 0
                # record.bottom_chord_af_female = 0
                # record.bottom_chord_il_normal = 0
                # record.bottom_chord_il_male = 0
                # record.bottom_chord_il_female = 0
                # record.length_bottom_chord_af_normal = 0
                # record.length_bottom_chord_af_male = 0
                # record.length_bottom_chord_af_female = 0
                # record.length_bottom_chord_il_normal = 0
                # record.length_bottom_chord_il_male = 0
                # record.length_bottom_chord_il_female = 0
                # record.no_v_support_bottom_chord = 0
                
    # @api.onchange('no_column_big_frame')
    # def _onchange_no_column_big_frame(self):
        # for record in self:
            # if int(record.no_column_big_frame) == 0:
                # record.no_anchor_frame_lines = 0
                # record.total_anchor_frames = 0
                # record.no_middle_columns = 0
                # record.no_quadraple_columns = 0
                # record.length_middle_column = 0
                # record.length_quadraple_column = 0
                
    # @api.onchange('thick_column')
    # def _onchange_thick_column(self):
        # for record in self:
            # if int(record.thick_column) == 0:
                # record.no_thick_columns = 0
                # record.length_thick_column =0

                
    # @api.onchange('is_arch_support_small_big_arch')
    # def _onchange_is_bottom_chord(self):
        # for record in self:
            # if not record.is_arch_support_small_big_arch:
                # record.arch_support_small_big_arch = 0
                # record.length_arch_support_small_big_arch = 0
                
    
    
    @api.depends(
        'total_span_length', 'width_front_span_coridoor', 'width_back_span_coridoor',
        'total_bay_length', 'width_front_bay_coridoor', 'width_back_bay_coridoor',
        'bay_width', 'span_width', 'top_ridge_height', 'column_height','no_front_bay_coridoor_hockeys',
        'no_back_bay_coridoor_hockeys', 'bay_side_border_purlin', 'no_of_bays', 
        'no_front_span_coridoor_hockeys', 'no_back_span_coridoor_hockeys', 'span_side_border_purlin', 
        'no_of_spans', 'no_column_big_frame','no_of_bays', 'no_of_spans', 'total_anchor_frames', 'is_arch_support_big', 
        'is_arch_support_small_big_arch', 'is_arch_support_small_small_arch', 
        'no_vent_big_arch_support_frame', 'no_vent_small_arch_support_frame', 'bay_length', 'span_length',
        'no_of_spans', 'front_back_c_c_cross_bracing_x', 'middle_c_c_cross_bracing_x', 
        'cross_bracing_column_arch', 'cross_bracing_column_bottom',
        'arch_middle_purlin_big_arch', 'arch_middle_purlin_big_arch_pcs', 
        'arch_middle_purlin_small_arch', 'arch_middle_purlin_small_arch_pcs', 
        'no_of_spans', 'no_of_bays',
        'gutter_ippf_full', 'gutter_ippf_drainage_extension', 'gutter_funnel_ippf', 'gutter_end_cap',
        'last_span_gutter', 'no_of_spans', 'no_of_bays', 'gutter_slope'
    )
    def action_calculate_process(self):
        for record in self:
            # Calculate span_length and bay_length
            record.span_length = record.total_span_length - (record.width_front_span_coridoor + record.width_back_span_coridoor)
            record.bay_length = record.total_bay_length - (record.width_front_bay_coridoor + record.width_back_bay_coridoor)

            # Calculate structure_size
            record.structure_size = (
                (record.span_length + record.width_front_span_coridoor + record.width_back_span_coridoor) *
                (record.bay_length + record.width_front_bay_coridoor + record.width_back_bay_coridoor)
            )

            # Calculate number of bays and spans
            record.no_of_bays = record.span_length / record.bay_width if record.bay_width else 0
            record.no_of_spans = record.bay_length / record.span_width if record.span_width else 0

            # Calculate bottom_height and arch_height
            record.bottom_height = record.column_height
            record.arch_height = record.top_ridge_height - record.column_height
            # Calculate Front Span Corridor
            record.no_asc = 0
            if record.width_front_span_coridoor > 0:
                record.no_asc = record.no_asc + 1
                record.length_front_span_coridoor = record.bay_length
                record.no_front_span_coridoor_hockeys = ((record.length_front_span_coridoor / record.span_width)  * (int(record.no_column_big_frame) + 1)) + 1
            else:
                record.no_front_span_coridoor_hockeys = 0
            

            # Calculate Back Span Corridor
            if record.width_back_span_coridoor > 0:
                record.no_asc = record.no_asc + 1
                record.length_back_span_coridoor = record.bay_length
                record.no_back_span_coridoor_hockeys = ((record.length_back_span_coridoor / record.span_width) * (int(record.no_column_big_frame) + 1)) + 1
            else:
                record.no_back_span_coridoor_hockeys = 0

            # Calculate Front Bay Corridor
            if record.width_front_bay_coridoor > 0:
                record.no_asc = record.no_asc + 1
                record.length_front_bay_coridoor = record.span_length
                record.no_front_bay_coridoor_hockeys = (record.length_front_bay_coridoor / record.bay_width) + 1
            else:
                record.no_front_bay_coridoor_hockeys = 0

            # Calculate Back Bay Corridor
            if record.width_back_bay_coridoor > 0:
                record.no_asc = record.no_asc + 1
                record.length_back_bay_coridoor = record.span_length
                record.no_back_bay_coridoor_hockeys = (record.length_back_bay_coridoor / record.bay_width) + 1
            else:
                record.no_back_bay_coridoor_hockeys = 0
            
            record.gutter_length = record.span_length
            #if record.span_width > 0 and record.bay_width > 0:
            #    record.no_of_border_columns = (
            #        ((record.length_front_span_coridoor / record.span_width) * (int(record.no_column_big_frame) + 1)) +
            #        ((record.length_back_span_coridoor / record.span_width) * (int(record.no_column_big_frame) + 1)) +
            #        (record.length_front_bay_coridoor / record.bay_width) +
            #        (record.length_back_bay_coridoor / record.bay_width) +
            #        4
            #    )
            #else:
            #    record.no_of_border_columns = 0
                
            # Total Hockeys
            record.no_total_hockeys = (record.no_front_span_coridoor_hockeys + 
                                       record.no_back_span_coridoor_hockeys + 
                                       record.no_front_bay_coridoor_hockeys + 
                                       record.no_back_bay_coridoor_hockeys)

            # Hockey Support
            record.no_hockey_support = record.support_hockeys * record.no_total_hockeys

            # Calculate anchor frames, columns, and other values
            record.total_anchor_frames = record.no_anchor_frame_lines * record.no_of_spans
            
            
            if int(record.no_column_big_frame) == 0:
                record.no_anchor_frame_lines = 0
            
            if int(record.no_column_big_frame) == 1:
                record.no_middle_columns = record.total_anchor_frames

            if int(record.no_column_big_frame) == 3:
                record.no_middle_columns = record.total_anchor_frames
                record.no_quadraple_columns = record.total_anchor_frames * 2

            if int(record.no_column_big_frame) == 2:
                record.no_quadraple_columns = record.total_anchor_frames * 2
                record.no_middle_columns = 0

            record.total_normal_frames = (record.no_of_spans * (record.no_of_bays + 1)) - record.total_anchor_frames

            if record.thick_column == '0':
                record.no_thick_columns = 0
            elif record.thick_column == '1':
                record.no_thick_columns = 4
            elif record.thick_column == '2':
                record.no_thick_columns = (record.no_of_bays + 1) * 2
            elif record.thick_column == '3':
                record.no_thick_columns = (record.no_of_spans + 1) * 2
            elif record.thick_column == '4':
                record.no_thick_columns = ((record.no_of_bays + 1) * 2) + ((record.no_of_spans + 1) * 2)

            record.no_main_columns = ((record.no_of_spans + 1) * (record.no_of_bays + 1)) - record.no_thick_columns

            # Bottom chord calculations based on column big frame and span width
            
            if record.no_column_big_frame == '0': #and record.span_width <= 6:
                record.bottom_chord_af_normal = record.total_anchor_frames
                record.bottom_chord_af_male = 0
                record.bottom_chord_af_female = 0
            elif record.no_column_big_frame == '0': #and record.span_width > 6:
                record.bottom_chord_af_normal = 0
                record.bottom_chord_af_male = record.total_anchor_frames
                record.bottom_chord_af_female = record.total_anchor_frames
            elif record.no_column_big_frame == '1':
                record.bottom_chord_af_normal = record.total_anchor_frames * 2
                record.bottom_chord_af_male = 0
                record.bottom_chord_af_female = 0
            elif record.no_column_big_frame == '2':
                record.bottom_chord_af_normal = record.total_anchor_frames * 3
                record.bottom_chord_af_male = 0
                record.bottom_chord_af_female = 0
            elif record.no_column_big_frame == '3':
                record.bottom_chord_af_normal = record.total_anchor_frames * 4
                record.bottom_chord_af_male = 0
                record.bottom_chord_af_female = 0

            if record.span_width <= 6:
                record.bottom_chord_il_normal = record.total_normal_frames
                record.bottom_chord_il_male = 0
                record.bottom_chord_il_female = 0
            else:
                record.bottom_chord_il_normal = 0
                record.bottom_chord_il_male = record.total_normal_frames
                record.bottom_chord_il_female = record.total_normal_frames

            record.no_v_support_bottom_chord = int(record.v_support_bottom_chord_frame) * record.total_normal_frames

            # Gable purlin calculations based on last span gutter
            if record.last_span_gutter:
                record.gable_purlin = 0
            else:
                record.gable_purlin = record.no_of_bays * 2

            #Calculate no_bay_side_border_purlin
            if record.no_front_bay_coridoor_hockeys > 0:
                record.no_bay_side_border_purlin = int(record.bay_side_border_purlin) * (record.no_front_bay_coridoor_hockeys - 1)
            else:
                record.no_bay_side_border_purlin = int(record.bay_side_border_purlin) * record.no_of_bays

            if record.no_back_bay_coridoor_hockeys > 0:
                record.no_bay_side_border_purlin += int(record.bay_side_border_purlin) * (record.no_back_bay_coridoor_hockeys - 1)
            else:
                record.no_bay_side_border_purlin += int(record.bay_side_border_purlin) * record.no_of_bays

            #Calculate no_span_side_border_purlin
            if record.no_front_span_coridoor_hockeys > 0:
                record.no_span_side_border_purlin = int(record.span_side_border_purlin) * (record.no_front_span_coridoor_hockeys - 1)
            else:
                record.no_span_side_border_purlin = int(record.span_side_border_purlin) * record.no_of_spans * (int(record.no_column_big_frame) + 1)

            if record.no_back_span_coridoor_hockeys > 0:
                record.no_span_side_border_purlin += int(record.span_side_border_purlin) * (record.no_back_span_coridoor_hockeys - 1)
            else:
                record.no_span_side_border_purlin += int(record.span_side_border_purlin) * record.no_of_spans * (int(record.no_column_big_frame) + 1)
                
            record.arch_big = (record.no_of_bays + 1) * record.no_of_spans
            record.arch_small = record.arch_big
            
            record.arch_support_staraight_middle = 0
            if record.is_bottom_chord:
                record.arch_support_staraight_middle = record.arch_big - record.total_anchor_frames

            record.arch_support_big = record.arch_big * 2 if record.is_arch_support_big else 0
            record.arch_support_small_big_arch = record.arch_big if record.is_arch_support_small_big_arch else 0
            record.arch_support_small_small_arch = record.arch_small if record.is_arch_support_small_small_arch else 0

            record.vent_big_arch_support = int(record.arch_big) * int(record.no_vent_big_arch_support_frame)
            record.vent_small_arch_support = record.no_of_bays * record.no_of_spans * int(record.no_vent_small_arch_support_frame)
            record.big_arch_purlin = record.no_of_bays * record.no_of_spans
            record.small_arch_purlin = int(record.big_arch_purlin)
            
            if record.big_arch_purlin > 0:
                record.length_big_arch_purlin = record.bay_width
                
            if record.small_arch_purlin > 0:
                record.length_small_arch_purlin = record.bay_width
                
            if record.gable_purlin > 0:
                record.length_gable_purlin = record.bay_width
            
            record.side_screen_roll_up_pipe = ceil((record.bay_length / 5.95) * 2) + ceil((record.span_length / 5.95) * 2)
            record.side_screen_roll_up_pipe_joiner = int(record.side_screen_roll_up_pipe) - 4
            
            if record.side_screen_guard:
                record.no_side_screen_guard = record.no_total_hockeys if record.no_total_hockeys > 0 else record.no_of_border_columns
                
            record.no_front_back_c_c_cross_bracing_x = record.front_back_c_c_cross_bracing_x * (record.no_of_spans + 1) * 4
            record.no_middle_c_c_cross_bracing_x = record.middle_c_c_cross_bracing_x * (record.no_of_spans + 1) * 2
            record.no_cross_bracing_column_arch = int(record.cross_bracing_column_arch) * (record.no_of_spans * 4)
            record.no_cross_bracing_column_bottom = record.cross_bracing_column_bottom * (record.no_of_spans * 4)
            
            if record.arch_middle_purlin_big_arch == 1:
                record.no_arch_middle_purlin_big_arch = 0
            elif record.arch_middle_purlin_big_arch == 2:
                record.no_arch_middle_purlin_big_arch = record.arch_middle_purlin_big_arch_pcs * 4
            elif record.arch_middle_purlin_big_arch == 3:
                record.no_arch_middle_purlin_big_arch = record.arch_middle_purlin_big_arch_pcs * (record.no_of_spans * 2)
            elif record.arch_middle_purlin_big_arch == 4:
                record.no_arch_middle_purlin_big_arch = record.arch_middle_purlin_big_arch_pcs * (record.no_of_bays * 2)
            elif record.arch_middle_purlin_big_arch == 5:
                record.no_arch_middle_purlin_big_arch = record.arch_middle_purlin_big_arch_pcs * ((record.no_of_spans * 2) + (record.no_of_bays * 2) - 4)
            elif record.arch_middle_purlin_big_arch == 6:
                record.no_arch_middle_purlin_big_arch = record.arch_middle_purlin_big_arch_pcs * (record.no_of_spans * record.no_of_bays)
                
            
            if record.arch_middle_purlin_small_arch == 0:
                record.no_arch_middle_purlin_small_arch = 0
            elif record.arch_middle_purlin_small_arch == 1:
                record.no_arch_middle_purlin_small_arch = record.arch_middle_purlin_small_arch_pcs * 4

            if record.gutter_ippf_full:
                if record.last_span_gutter:
                    record.no_gutter_ippf_full = (record.no_of_spans + 1) * record.no_of_bays
                else:
                    record.no_gutter_ippf_full = (record.no_of_spans - 1) * record.no_of_bays

            if record.gutter_ippf_drainage_extension:
                if record.last_span_gutter:
                    record.no_gutter_ippf_drainage_ext = (record.no_of_spans + 1) * int(record.gutter_slope)
                else:
                    record.no_gutter_ippf_drainage_ext = (record.no_of_spans - 1) * int(record.gutter_slope)

            if record.gutter_funnel_ippf:
                if record.last_span_gutter:
                    record.no_gutter_funnel_ippf_funnel = (record.no_of_spans + 1) * int(record.gutter_slope)
                else:
                    record.no_gutter_funnel_ippf_funnel = (record.no_of_spans - 1) * int(record.gutter_slope)

            if record.gutter_end_cap and record.gutter_funnel_ippf and int(record.gutter_slope) == 1:
                if record.last_span_gutter:
                    record.no_gutter_end_cap = record.no_of_spans + 1
                else:
                    record.no_gutter_end_cap = record.no_of_spans - 1
                    
                    
            if record.no_middle_columns >0:
                record.length_middle_column = record.top_ridge_height
                
            if record.no_quadraple_columns >0:
                record.length_quadraple_column = record.top_ridge_height
                    
            if record.no_main_columns >0:
                record.length_main_column = record.column_height
                
            if record.no_thick_columns >0:
                record.length_thick_column = record.column_height
            
            if record.no_front_span_coridoor_hockeys > 0:
                record.length_front_span_coridoor_hockey = 1 + sqrt(record.width_front_span_coridoor ** 2 + record.column_height ** 2)
                
            if record.no_back_span_coridoor_hockeys > 0:
                record.length_back_span_coridoor_hockey = 1 + sqrt(record.width_back_span_coridoor ** 2 + record.column_height ** 2)
                
            if record.no_front_bay_coridoor_hockeys > 0:
                record.length_front_bay_coridoor_hockey = 1 + sqrt(record.width_front_bay_coridoor ** 2 + record.column_height ** 2)
                
            if record.no_back_bay_coridoor_hockeys > 0:
                record.length_back_bay_coridoor_hockey = 1 + sqrt(record.width_back_bay_coridoor ** 2 + record.column_height ** 2)
            
            record.length_bottom_chord_af_normal = 0 
            if record.bottom_chord_af_normal > 0:
                record.length_bottom_chord_af_normal = record.span_width/(1+int(record.no_column_big_frame))
        
            record.length_bottom_chord_af_male = 0 
            if record.bottom_chord_af_male > 0:
                record.length_bottom_chord_af_male = record.span_width/2
                
            record.length_bottom_chord_af_female = 0 
            if record.bottom_chord_af_female > 0:
                record.length_bottom_chord_af_female = record.span_width/2
            
            record.length_bottom_chord_il_normal = 0 
            if record.bottom_chord_il_normal > 0:
                record.length_bottom_chord_il_normal = record.span_width
        
            record.length_bottom_chord_il_male = 0 
            if record.bottom_chord_il_male > 0:
                record.length_bottom_chord_il_male = record.span_width/2
                
            record.length_bottom_chord_il_female = 0 
            if record.bottom_chord_il_female > 0:
                record.length_bottom_chord_il_female = record.span_width/2
            
            record.length_arch_support_staraight_middle = 0
            if record.arch_support_staraight_middle > 0:    
                record.length_arch_support_staraight_middle = record.top_ridge_height - record.column_height
                
            record.length_bay_side_border_purlin = 0
            if record.no_bay_side_border_purlin > 0:    
                record.length_bay_side_border_purlin = record.bay_width
                
            record.length_span_side_border_purlin = 0
            if record.no_span_side_border_purlin > 0:    
                record.length_span_side_border_purlin = record.span_width/ (int(record.no_column_big_frame) + 1)
                
            record.length_side_screen_roll_up_pipe = 0
            if record.side_screen_roll_up_pipe > 0:    
                record.length_side_screen_roll_up_pipe = 6

            record.length_arch_middle_purlin_big_arch = 0
            if record.no_arch_middle_purlin_big_arch > 0:    
                record.length_arch_middle_purlin_big_arch = record.bay_width
                
            record.length_arch_middle_purlin_small_arch = 0
            if record.no_arch_middle_purlin_small_arch > 0:    
                record.length_arch_middle_purlin_small_arch = record.bay_width
                
            record.length_gutter_ippf_full = 0 
            if record.no_gutter_ippf_full > 0:
                record.length_gutter_ippf_full = record.bay_width +.04 
                
            record.no_side_screen_guard_box_pipe = 0
            if record.no_side_screen_guard_box > 0:    
                record.no_side_screen_guard_box_pipe =  record.no_side_screen_guard_box * 2
                record.no_side_screen_guard_box_h_pipe = record.no_side_screen_guard_box * 2
                record.length_side_screen_guard_box_pipe = record.column_height
                if record.no_total_hockeys > 0:
                    record.length_side_screen_guard_box_pipe = record.column_height+1.5
                
            record.side_screen_guard_spacer = (record.no_side_screen_guard *2) + (record.no_side_screen_guard_box * 4)
        
        
        
    def print_report(self):
        return self.env.ref('greenh.report_print_green_master').report_action(self)
        
   
        
class PipeType(models.Model):
    _name = 'pipe.type'
    _description = 'Pipe Type'

    name = fields.Char(string='Pipe Type', required=True)

# Master for Pipe Size
class PipeSize(models.Model):
    _name = 'pipe.size'
    _description = 'Pipe Size'

    name = fields.Char(string='Pipe Size', required=True)
    size_in_mm = fields.Float(string='Size in mm', required=True)

# Master for Wall Thickness
class PipeWallThickness(models.Model):
    _name = 'pipe.wall_thickness'
    _description = 'Pipe Wall Thickness'

    name = fields.Char(string='Wall Thickness', required=True)
    thickness_in_mm = fields.Float(string='Thickness in mm', required=True)

# Main Pipe Management model
class Pipe(models.Model):
    _name = 'pipe.management'
    _description = 'Pipe Management'

    name = fields.Many2one('pipe.type', string='Pipe Type', required=True)
    pipe_size = fields.Many2one('pipe.size', string='Pipe Size (in mm)', required=True)
    wall_thickness = fields.Many2one('pipe.wall_thickness', string='Wall Thickness (in mm)', required=True)
    weight = fields.Float(string='Weight (in kg)', required=True)
    rate = fields.Float(string='Rate (per kg)', required=True)
    total_cost = fields.Float(string='Total Cost', compute='_compute_total_cost', store=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)
    
    @api.depends('weight', 'rate')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.weight * record.rate
    
    
        
    @api.depends('pipe_size','wall_thickness')
    def _compute_display_name(self):
        for record in self:
            # Ensure the fields have values before concatenating
            if record.name and record.pipe_size and record.wall_thickness:
                record.display_name = f'{record.name.name} / Size: {record.pipe_size.size_in_mm} mm / Thickness: {record.wall_thickness.thickness_in_mm} mm'
            else:
                # Fallback to just Pipe Type if other fields are missing
                record.display_name = record.name.name or 'Unnamed Pipe'
                
    # Constraint to prevent duplication
    _sql_constraints = [
        ('unique_pipe_combination', 
         'unique(name, pipe_size, wall_thickness)', 
         'A pipe with this type, size, and wall thickness already exists.')
    ]

    @api.constrains('name', 'pipe_size', 'wall_thickness')
    def _check_duplicate_pipe(self):
        for record in self:
            duplicates = self.search([
                ('name', '=', record.name.id),
                ('pipe_size', '=', record.pipe_size.id),
                ('wall_thickness', '=', record.wall_thickness.id),
                ('id', '!=', record.id)  # Exclude the current record
            ])
            if duplicates:
                raise ValidationError(_('A pipe with this type, size, and wall thickness already exists.'))            
