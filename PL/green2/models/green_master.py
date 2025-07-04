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
            record.display_name = str(record.length_value)

class ComponentLine(models.Model):
    _name = 'component.line'
    _description = 'Component Line'
    
    green_master_id = fields.Many2one('green.master', string='Green Master', ondelete='cascade')
    section = fields.Selection([
        ('asc', 'ASC Components'),
        ('frame', 'Frame Components'),
        ('truss', 'Truss Components'),
        ('lower', 'Lower Section Components'),
    ], string='Section', required=True)
    
    name = fields.Char(string='Component Name', required=True)
    required = fields.Boolean(string='Required', default=True)
    nos = fields.Integer(string='Nos', default=0)
    length = fields.Float(string='Length', default=0.0)
    pipe_id = fields.Many2one('pipe.management', string='Pipe Type')
    
    # Computed fields for pipe details
    pipe_type = fields.Char(string='Pipe Type', related='pipe_id.name.name', readonly=True)
    pipe_size = fields.Float(string='Size (mm)', related='pipe_id.pipe_size.size_in_mm', readonly=True)
    wall_thickness = fields.Float(string='WT (mm)', related='pipe_id.wall_thickness.thickness_in_mm', readonly=True)
    weight_per_unit = fields.Float(string='Weight/Unit', related='pipe_id.weight', readonly=True)
    rate_per_kg = fields.Float(string='Rate/Kg', related='pipe_id.rate', readonly=True)
    
    # Calculations
    total_length = fields.Float(string='Total Length', compute='_compute_totals', store=True)
    total_weight = fields.Float(string='Total Weight', compute='_compute_totals', store=True)
    total_cost = fields.Float(string='Total Cost', compute='_compute_totals', store=True)
    
    @api.depends('nos', 'length', 'weight_per_unit', 'rate_per_kg')
    def _compute_totals(self):
        for record in self:
            record.total_length = record.nos * record.length
            record.total_weight = record.total_length * record.weight_per_unit
            record.total_cost = record.total_weight * record.rate_per_kg

class GreenMaster(models.Model):
    _name = 'green.master'
    _description = 'Greenhouse Master'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Basic Information
    customer = fields.Char('Customer', size=50)
    address = fields.Char('Address', size=200)
    city = fields.Char('City', size=50)
    mobile = fields.Char('Mobile', size=13)
    email = fields.Char('Email', size=40)
    reference = fields.Char('Reference', size=300)
    
    # Structure Details
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
    top_ridge_height = fields.Float('Top Ridge Height', default=0.00)
    column_height = fields.Float('Column Height', default=0.00)
    bottom_height = fields.Float('Bottom Height', default=0.00)
    arch_height = fields.Float('Arch Height', default=0.00)
    big_arch_length = fields.Float('Big Arch Length', default=0.00)
    small_arch_length = fields.Float('Small Arch Length', default=0.00)
    
    # ASC Settings
    is_side_coridoors = fields.Boolean('Is ASC', default=False)
    width_front_span_coridoor = fields.Float('Width Front Span ASC', default=0.00)
    width_back_span_coridoor = fields.Float('Width Back Span ASC', default=0.00)
    width_front_bay_coridoor = fields.Float('Width Left Bay ASC', default=0.00)
    width_back_bay_coridoor = fields.Float('Width Right Bay ASC', default=0.00)
    support_hockeys = fields.Integer('Support per Hockey', default=0)
    
    # Frame Settings
    no_column_big_frame = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2'),('3', '3')
    ], string='No of Big Column per Anchor Frame', required=True, default='0')
    no_anchor_frame_lines = fields.Integer('Number of Anchor Frame Lines', default=0)
    thick_column = fields.Selection([
        ('0', '0'),( '1','4 Corners'),( '2','Both Bay Side'),( '3','Both Span Side'),( '4','All 4 Side')
    ], string='Thick Column Option', required=True, default='0')
    
    # Truss Settings
    is_bottom_chord = fields.Boolean('Is Bottom Chord Required ?', default=False)
    v_support_bottom_chord_frame = fields.Selection([
        ('0', '0'),('2', '2')],'V Support Bottom Chord per Frame', default='0')
    is_arch_support_big = fields.Boolean('Is Arch Support Big (Both Arches) Required ?', default=False)
    is_arch_support_small_big_arch = fields.Boolean('Is Arch Support Small for Bigger Arch Required?', default=False)
    is_arch_support_small_small_arch = fields.Boolean('Is Arch Support Small for Smaller Arch Required?', default=False)
    no_vent_big_arch_support_frame = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2'),('3', '3')], string='Vent Support for Big Arch per Frame', required=True, default='0')
    no_vent_small_arch_support_frame = fields.Selection([
        ('0', '0'),('2', '2')], string='Vent Support for Small Arch per Frame', required=True, default='0')
    bay_side_border_purlin = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2')], string='Bay Side Border Purlin', required=True, default='0')
    span_side_border_purlin = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2')], string='Span Side Border Purlin', required=True, default='0')
    
    # Lower Section Settings
    side_screen_guard = fields.Boolean('Side Screen Guard', default=False)
    side_screen_guard_box = fields.Boolean('Side Screen Guard Box', default=False)
    no_side_screen_guard_box = fields.Integer('Number of Side Screen Guard Box', default=0)
    front_back_c_c_cross_bracing_x = fields.Boolean('Front & Back Column to Column Cross bracing X', default=False)
    middle_c_c_cross_bracing_x = fields.Integer('No of Internal Column lines for Column to Column Cross Bracing X', default=0)
    cross_bracing_column_arch = fields.Boolean('Cross Bracing Column to Arch', default=0)
    cross_bracing_column_bottom = fields.Boolean('Cross Bracing Column to Bottom Chord', default=False)
    arch_middle_purlin_big_arch = fields.Selection([
        ('0', '0'),( '1','4 Corners'),( '2','Front & Back'),( '3','Both Sides'),( '4','All 4 Side'),( '5','4 Sides'),( '6','All')], string='Arch Middle Purlin Big Arch', required=True, default='0')
    arch_middle_purlin_big_arch_pcs = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2')], string='Arch Middle Purlin Big Arch Pcs', required=True, default='0')
    arch_middle_purlin_small_arch = fields.Selection([
        ('0', '0'),( '1','4 Corners'),( '2','Front & Back'),( '3','Both Sides'),( '4','All 4 Side'),( '5','4 Sides'),( '6','All')], string='Arch Middle Purlin Small Arch', required=True, default='0')
    arch_middle_purlin_small_arch_pcs = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2')], string='Arch Middle Purlin Small Arch Pcs', required=True, default='0')
    gutter_ippf_full = fields.Boolean('Gutter IPPF Full', default=False)
    gutter_ippf_drainage_extension = fields.Boolean('Gutter IPPF Drainage Extension', default=False)
    gutter_funnel_ippf = fields.Boolean('Gutter Funnel IPPF', default=False)
    gutter_end_cap = fields.Boolean('Gutter End Cap', default=False)
    
    # Component Lines
    asc_component_ids = fields.One2many('component.line', 'green_master_id', 
                                       domain=[('section', '=', 'asc')], 
                                       string='ASC Components')
    frame_component_ids = fields.One2many('component.line', 'green_master_id', 
                                         domain=[('section', '=', 'frame')], 
                                         string='Frame Components')
    truss_component_ids = fields.One2many('component.line', 'green_master_id', 
                                         domain=[('section', '=', 'truss')], 
                                         string='Truss Components')
    lower_component_ids = fields.One2many('component.line', 'green_master_id', 
                                         domain=[('section', '=', 'lower')], 
                                         string='Lower Section Components')
    
    # Summary Totals
    total_asc_cost = fields.Float('Total ASC Cost', compute='_compute_section_totals', store=True)
    total_frame_cost = fields.Float('Total Frame Cost', compute='_compute_section_totals', store=True)
    total_truss_cost = fields.Float('Total Truss Cost', compute='_compute_section_totals', store=True)
    total_lower_cost = fields.Float('Total Lower Cost', compute='_compute_section_totals', store=True)
    grand_total_cost = fields.Float('Grand Total Cost', compute='_compute_section_totals', store=True)
    
    @api.depends('asc_component_ids.total_cost', 'frame_component_ids.total_cost', 
                 'truss_component_ids.total_cost', 'lower_component_ids.total_cost')
    def _compute_section_totals(self):
        for record in self:
            record.total_asc_cost = sum(record.asc_component_ids.mapped('total_cost'))
            record.total_frame_cost = sum(record.frame_component_ids.mapped('total_cost'))
            record.total_truss_cost = sum(record.truss_component_ids.mapped('total_cost'))
            record.total_lower_cost = sum(record.lower_component_ids.mapped('total_cost'))
            record.grand_total_cost = (record.total_asc_cost + record.total_frame_cost + 
                                     record.total_truss_cost + record.total_lower_cost)

    def action_calculate_process(self):
        for record in self:
            # Clear existing component lines
            record.asc_component_ids.unlink()
            record.frame_component_ids.unlink()
            record.truss_component_ids.unlink()
            record.lower_component_ids.unlink()
            
            # Calculate basic dimensions
            record.span_length = record.total_span_length - (record.width_front_span_coridoor + record.width_back_span_coridoor)
            record.bay_length = record.total_bay_length - (record.width_front_bay_coridoor + record.width_back_bay_coridoor)
            record.structure_size = (record.span_length + record.width_front_span_coridoor + record.width_back_span_coridoor) * (record.bay_length + record.width_front_bay_coridoor + record.width_back_bay_coridoor)
            record.no_of_bays = record.span_length / record.bay_width if record.bay_width else 0
            record.no_of_spans = record.bay_length / record.span_width if record.span_width else 0
            record.bottom_height = record.column_height
            record.arch_height = record.top_ridge_height - record.column_height
            record.gutter_length = record.span_length
            
            # Calculate component lines for each section
            record._calculate_components()
    
    def _calculate_components(self):
        """Calculate all components"""
        component_vals = []
        
        # ASC Components
        if self.is_side_coridoors and self.support_hockeys > 0:
            total_hockeys = 0
            if self.width_front_span_coridoor > 0:
                total_hockeys += ((self.bay_length / self.span_width) * (int(self.no_column_big_frame) + 1)) + 1
            if self.width_back_span_coridoor > 0:
                total_hockeys += ((self.bay_length / self.span_width) * (int(self.no_column_big_frame) + 1)) + 1
            if self.width_front_bay_coridoor > 0:
                total_hockeys += (self.span_length / self.bay_width) + 1
            if self.width_back_bay_coridoor > 0:
                total_hockeys += (self.span_length / self.bay_width) + 1
                
            component_vals.append({
                'green_master_id': self.id,
                'section': 'asc',
                'name': 'ASC Pipe Support',
                'required': True,
                'nos': self.support_hockeys * total_hockeys,
                'length': 1.5,
            })
        
        # Frame Components
        total_anchor_frames = self.no_anchor_frame_lines * self.no_of_spans
        
        if int(self.no_column_big_frame) == 1:
            component_vals.append({
                'green_master_id': self.id,
                'section': 'frame',
                'name': 'Middle Columns',
                'required': True,
                'nos': total_anchor_frames,
                'length': self.top_ridge_height,
            })
        
        # Main Columns
        no_thick_columns = 0
        if self.thick_column == '1':
            no_thick_columns = 4
        elif self.thick_column == '2':
            no_thick_columns = (self.no_of_bays + 1) * 2
        
        no_main_columns = ((self.no_of_spans + 1) * (self.no_of_bays + 1)) - no_thick_columns
        if no_main_columns > 0:
            component_vals.append({
                'green_master_id': self.id,
                'section': 'frame',
                'name': 'Main Columns',
                'required': True,
                'nos': no_main_columns,
                'length': self.column_height,
            })
        
        # Truss Components
        arch_big = (self.no_of_bays + 1) * self.no_of_spans
        component_vals.extend([
            {
                'green_master_id': self.id,
                'section': 'truss',
                'name': 'Big Arch',
                'required': True,
                'nos': arch_big,
                'length': self.big_arch_length,
            },
            {
                'green_master_id': self.id,
                'section': 'truss',
                'name': 'Small Arch',
                'required': True,
                'nos': arch_big,
                'length': self.small_arch_length,
            }
        ])
        
        # Lower Section Components
        side_screen_pipes = ceil((self.bay_length / 5.95) * 2) + ceil((self.span_length / 5.95) * 2)
        component_vals.append({
            'green_master_id': self.id,
            'section': 'lower',
            'name': 'Side Screen Roll Up Pipe',
            'required': True,
            'nos': side_screen_pipes,
            'length': 6.0,
        })
        
        # Create all component lines
        self.env['component.line'].create(component_vals)

    def print_report(self):
        return self.env.ref('greenh.report_print_green_master').report_action(self)

# Pipe Models
class PipeType(models.Model):
    _name = 'pipe.type'
    _description = 'Pipe Type'
    name = fields.Char(string='Pipe Type', required=True)

class PipeSize(models.Model):
    _name = 'pipe.size'
    _description = 'Pipe Size'
    name = fields.Char(string='Pipe Size', required=True)
    size_in_mm = fields.Float(string='Size in mm', required=True)

class PipeWallThickness(models.Model):
    _name = 'pipe.wall_thickness'
    _description = 'Pipe Wall Thickness'
    name = fields.Char(string='Wall Thickness', required=True)
    thickness_in_mm = fields.Float(string='Thickness in mm', required=True)

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
            if record.name and record.pipe_size and record.wall_thickness:
                record.display_name = f'{record.name.name} / Size: {record.pipe_size.size_in_mm} mm / Thickness: {record.wall_thickness.thickness_in_mm} mm'
            else:
                record.display_name = record.name.name or 'Unnamed Pipe'
    
    _sql_constraints = [
        ('unique_pipe_combination', 
         'unique(name, pipe_size, wall_thickness)', 
         'A pipe with this type, size, and wall thickness already exists.')
    ]