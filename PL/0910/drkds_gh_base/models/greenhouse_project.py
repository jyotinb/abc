from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class GreenhouseProject(models.Model):
    _name = 'greenhouse.project'
    _description = 'Greenhouse Project'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Name', compute='_compute_name', store=True)
    customer = fields.Char('Customer', tracking=True)
    address = fields.Text('Address')
    city = fields.Char('City')
    mobile = fields.Char('Mobile')
    email = fields.Char('Email')
    reference = fields.Text('Reference')
    
    @api.depends('customer', 'city')
    def _compute_name(self):
        for rec in self:
            parts = []
            if rec.customer:
                parts.append(rec.customer)
            if rec.city:
                parts.append(f"({rec.city})")
            rec.name = ' '.join(parts) or 'New Project'
    
    # Structure Configuration
    structure_type = fields.Selection([
        ('NVPH', 'NVPH'),
        ('NVPH2', 'NVPH2'),
    ], string='Structure Type', default='NVPH', required=True, tracking=True)
    
    plot_size = fields.Char('Plot Size')
    
    # Dimensions
    total_span_length = fields.Float('Total Span Length', required=True, tracking=True)
    total_bay_length = fields.Float('Total Bay Length', required=True, tracking=True)
    span_width = fields.Float('Span Width', default=8.0, required=True, tracking=True)
    bay_width = fields.Float('Bay Width', default=4.0, required=True, tracking=True)
    
    # Heights
    top_ridge_height = fields.Float('Top Ridge Height', required=True, tracking=True)
    column_height = fields.Float('Column Height', required=True, tracking=True)
    big_arch_length = fields.Float('Big Arch Length', required=True, tracking=True)
    small_arch_length = fields.Float('Small Arch Length', required=True, tracking=True)
    foundation_length = fields.Float('Foundation Length', default=0.6, tracking=True)
    
    # Calculated fields
    span_length = fields.Float('Span Length', compute='_compute_dimensions', store=True)
    bay_length = fields.Float('Bay Length', compute='_compute_dimensions', store=True)
    structure_size = fields.Float('Structure Size', compute='_compute_dimensions', store=True)
    no_of_bays = fields.Integer('Number of Bays', compute='_compute_dimensions', store=True)
    no_of_spans = fields.Integer('Number of Spans', compute='_compute_dimensions', store=True)
    bottom_height = fields.Float('Bottom Height', compute='_compute_dimensions', store=True)
    arch_height = fields.Float('Arch Height', compute='_compute_dimensions', store=True)
    gutter_length = fields.Float('Gutter Length', compute='_compute_dimensions', store=True)
    
    @api.depends('total_span_length', 'total_bay_length', 'span_width', 'bay_width', 'column_height', 'top_ridge_height')
    def _compute_dimensions(self):
        for rec in self:
            rec.span_length = rec.total_span_length
            rec.bay_length = rec.total_bay_length
            rec.structure_size = rec.total_span_length * rec.total_bay_length
            rec.no_of_bays = int(rec.span_length / rec.bay_width) if rec.bay_width else 0
            rec.no_of_spans = int(rec.bay_length / rec.span_width) if rec.span_width else 0
            rec.bottom_height = rec.column_height
            rec.arch_height = rec.top_ridge_height - rec.column_height
            rec.gutter_length = rec.span_length
    
    # Configuration fields for modules
    is_side_coridoors = fields.Boolean('Enable ASC', default=False, tracking=True)
    no_column_big_frame = fields.Selection([
        ('0', '0'), ('1', '1'), ('2', '2'), ('3', '3')
    ], string='No of Big Column per Anchor Frame', default='0', tracking=True)
    no_anchor_frame_lines = fields.Integer('Number of Anchor Frame Lines', default=0, tracking=True)
    thick_column = fields.Selection([
        ('0', 'None'),
        ('1', '4 Corners'),
        ('2', 'Both Bay Side'),
        ('3', 'Both Span Side'),
        ('4', 'All 4 Side')
    ], string='Thick Column Option', default='0', tracking=True)
    is_bottom_chord = fields.Boolean('Bottom Chord Required', default=False, tracking=True)
    bottom_chord_type = fields.Selection([
        ('male_female', 'Male-Female'),
        ('singular', 'Singular')
    ], string='Bottom Chord Type', default='male_female')
    gutter_type = fields.Selection([
        ('continuous', 'Continuous'),
        ('ippf', 'IPPF System')
    ], string='Gutter Type', default='continuous', tracking=True)
    gutter_slope = fields.Selection([
        ('1', '1'), ('2', '2')
    ], string='Gutter Slope', default='1', tracking=True)
    last_span_gutter = fields.Boolean('Last Span Gutter', default=False, tracking=True)
    last_span_gutter_length = fields.Integer('Last Span Gutter Length', default=0, tracking=True)
    side_screen_guard = fields.Boolean('Side Screen Guard', default=False, tracking=True)
    side_screen_guard_box = fields.Boolean('Side Screen Guard Box', default=False, tracking=True)
    no_of_curtains = fields.Integer('Number of Curtains', default=1, tracking=True)
    
    # Components
    component_line_ids = fields.One2many('greenhouse.component.line', 'project_id', string='Components')
    
    # Cost
    grand_total_cost = fields.Float('Grand Total Cost', compute='_compute_total_cost', store=True)
    
    @api.depends('component_line_ids.total_cost')
    def _compute_total_cost(self):
        for rec in self:
            rec.grand_total_cost = sum(rec.component_line_ids.mapped('total_cost'))
    
    def _calculate_all_components(self):
        """Base calculation method - modules extend this"""
        _logger.info(f"Calculating components for project {self.id}")
        return True
    
    def action_calculate_components(self):
        """Calculate all components"""
        self.component_line_ids.unlink()
        self._calculate_all_components()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Calculated {len(self.component_line_ids)} components',
                'type': 'success',
            }
        }
    
    @api.constrains('total_span_length', 'total_bay_length', 'span_width', 'bay_width')
    def _check_dimensions(self):
        for rec in self:
            if rec.total_span_length <= 0 or rec.total_bay_length <= 0:
                raise ValidationError("Dimensions must be positive")
            if rec.span_width <= 0 or rec.bay_width <= 0:
                raise ValidationError("Width values must be positive")
            if rec.span_width > rec.total_span_length:
                raise ValidationError("Span width cannot exceed total span length")
            if rec.bay_width > rec.total_bay_length:
                raise ValidationError("Bay width cannot exceed total bay length")
    
    @api.constrains('column_height', 'top_ridge_height')
    def _check_heights(self):
        for rec in self:
            if rec.column_height <= 0 or rec.top_ridge_height <= 0:
                raise ValidationError("Heights must be positive")
            if rec.column_height >= rec.top_ridge_height:
                raise ValidationError("Column height must be less than top ridge height")
