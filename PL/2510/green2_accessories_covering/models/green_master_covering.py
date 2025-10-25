# -*- coding: utf-8 -*-
from odoo import models, fields, api
from math import ceil, sqrt
import logging

_logger = logging.getLogger(__name__)

class CoveringWidth(models.Model):
    """Available covering material widths"""
    _name = 'covering.width'
    _description = 'Available Covering Material Widths'
    _order = 'width_value asc'
    
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    width_value = fields.Float(string='Width (m)', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    notes = fields.Text(string='Notes')
    
    @api.depends('width_value')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.width_value}m" if record.width_value else "0.0m"
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.width_value}m" if record.width_value else "0.0m"
            result.append((record.id, name))
        return result


class ApronWidth(models.Model):
    """Available apron material widths with pricing"""
    _name = 'apron.width'
    _description = 'Apron Material Width Master'
    _order = 'width_value asc'
    
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    width_value = fields.Float(string='Width (m)', required=True, tracking=True)
    unit_price = fields.Float(string='Price per m²', default=0.0, tracking=True,
                              help="Price per square meter for this width")
    active = fields.Boolean(string='Active', default=True, tracking=True)
    notes = fields.Text(string='Notes')
    
    @api.depends('width_value')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.width_value}m" if record.width_value else "0.0m"
    
    def name_get(self):
        result = []
        for record in self:
            price_info = f" - ₹{record.unit_price}/m²" if record.unit_price > 0 else ""
            name = f"{record.width_value}m{price_info}" if record.width_value else "0.0m"
            result.append((record.id, name))
        return result
    
    _sql_constraints = [
        ('unique_apron_width', 'unique(width_value)', 
         'An apron width with this value already exists.')
    ]


class InsectNetWidth(models.Model):
    """Available insect net widths with pricing"""
    _name = 'insect.net.width'
    _description = 'Insect Net Width Master'
    _order = 'width_value asc'
    
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    width_value = fields.Float(string='Width (m)', required=True, tracking=True)
    unit_price = fields.Float(string='Price per m²', default=0.0, tracking=True,
                              help="Price per square meter for this width")
    active = fields.Boolean(string='Active', default=True, tracking=True)
    notes = fields.Text(string='Notes')
    
    @api.depends('width_value')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.width_value}m" if record.width_value else "0.0m"
    
    def name_get(self):
        result = []
        for record in self:
            price_info = f" - ₹{record.unit_price}/m²" if record.unit_price > 0 else ""
            name = f"{record.width_value}m{price_info}" if record.width_value else "0.0m"
            result.append((record.id, name))
        return result
    
    _sql_constraints = [
        ('unique_insect_net_width', 'unique(width_value)', 
         'An insect net width with this value already exists.')
    ]


class GreenMasterCovering(models.Model):
    _inherit = 'green.master'
    
    # Covering configuration fields
    calculate_covering_material = fields.Boolean(
        string='Calculate Covering Material?',
        default=False,
        tracking=True,
        help="Enable to calculate covering material components"
    )
    
    is_apron = fields.Boolean(
        string='Is Apron',
        default=False,
        tracking=True,
        help="Affects front and back span covering width calculation"
    )
    
    apron_width_id = fields.Many2one(
        'apron.width',
        string='Apron Width',
        tracking=True,
        help="Select apron width with pricing"
    )
    
    calculate_insect_net = fields.Boolean(
        string='Calculate Insect Net?',
        default=False,
        tracking=True,
        help="Enable insect net covering calculation"
    )
    
    insect_net_width_id = fields.Many2one(
        'insect.net.width',
        string='Insect Net Width',
        tracking=True,
        help="Select insect net width with pricing"
    )
    
    # Covering component collections (using profiles section)
    covering_component_ids = fields.One2many(
        'accessories.component.line',
        'green_master_id',
        domain=[('section', '=', 'profiles'), ('name', 'ilike', 'Covering')],
        string='Covering Components'
    )
    
    # Cost field for covering
    total_covering_cost = fields.Float(
        'Total Covering Cost',
        compute='_compute_covering_cost',
        store=True,
        tracking=True
    )
    
    @api.depends('covering_component_ids.total_cost')
    def _compute_covering_cost(self):
        """Compute total cost for covering components"""
        for record in self:
            record.total_covering_cost = sum(record.covering_component_ids.mapped('total_cost'))
    
    def _calculate_all_accessories(self):
        """Extend to add covering calculations"""
        super()._calculate_all_accessories()
        if self.calculate_covering_material:
            self._calculate_covering_components()
    
    def _calculate_covering_components(self):
        """Calculate only covering-related components"""
        _logger.info("=== CALCULATING COVERING COMPONENTS ===")
        
        # Clear existing covering components
        existing_covering = self.env['accessories.component.line'].search([
            ('green_master_id', '=', self.id),
            ('section', '=', 'profiles'),
            ('name', 'ilike', 'Covering')
        ])
        if existing_covering:
            existing_covering.unlink()
        
        # Calculate each covering type
        self._calculate_big_arch_covering()
        self._calculate_small_arch_covering()
        self._calculate_front_span_covering()
        self._calculate_back_span_covering()
        self._calculate_front_bay_covering()
        self._calculate_back_bay_covering()
        self._calculate_gable_covering()
        self._calculate_side_corridor_corner_covering()
        self._calculate_entry_chambers_covering()
        self._calculate_apron_covering()
        self._calculate_insect_net_covering()
        
        _logger.info(f"Covering calculation complete. Total cost: {self.total_covering_cost}")
    
    def _calculate_big_arch_covering(self):
        """Calculate Big Arch Plastic covering"""
        if self.no_of_spans <= 0 or self.span_length <= 0 or self.big_arch_length <= 0:
            _logger.warning("Insufficient data for Big Arch covering calculation")
            return
        
        # Length = Span Length + 1
        length = self.span_length + 1
        
        # Nos = No of Spans
        nos = self.no_of_spans
        
        # Width = Big Arch Length (rounded up to available width)
        required_width = self.big_arch_length
        width = self._round_up_to_available_width(required_width)
        
        # Quantity = Width × Length × Nos (square meters)
        quantity = width * length * nos
        
        # Create component
        component_name = "Big Arch Plastic Covering"
        size_spec = f"{width}m width"
        
        self._create_covering_component(
            'profiles',
            component_name,
            length,
            width,
            nos,
            quantity,
            size_spec
        )
        
        _logger.info(f"Created Big Arch Covering: {nos} rolls, {length:.2f}m × {width:.2f}m = {quantity:.2f} m²")
    
    def _calculate_small_arch_covering(self):
        """Calculate Small Arch Plastic covering"""
        if self.no_of_spans <= 0 or self.span_length <= 0 or self.small_arch_length <= 0:
            _logger.warning("Insufficient data for Small Arch covering calculation")
            return
        
        # Length = Span Length + 1
        length = self.span_length + 1
        
        # Nos = No of Spans
        nos = self.no_of_spans
        
        # Width = Small Arch Length (rounded up to available width)
        required_width = self.small_arch_length
        width = self._round_up_to_available_width(required_width)
        
        # Quantity = Width × Length × Nos (square meters)
        quantity = width * length * nos
        
        # Create component
        component_name = "Small Arch Plastic Covering"
        size_spec = f"{width}m width"
        
        self._create_covering_component(
            'profiles',
            component_name,
            length,
            width,
            nos,
            quantity,
            size_spec
        )
        
        _logger.info(f"Created Small Arch Covering: {nos} rolls, {length:.2f}m × {width:.2f}m = {quantity:.2f} m²")
    
    def _calculate_front_span_covering(self):
        """Calculate Front Span Plastic covering"""
        if self.bay_length <= 0:
            _logger.warning("Insufficient data for Front Span covering calculation")
            return
        
        # Length = Bay Length + 1
        length = self.bay_length + 1
        
        # Nos = 1
        nos = 1
        
        # Width calculation based on ASC and Apron
        # Check if front span has ASC by checking width_front_span_coridoor
        if hasattr(self, 'width_front_span_coridoor') and self.width_front_span_coridoor > 0:
            asc_length = self._get_asc_length()
            if self.is_apron:
                width = asc_length - 1 if asc_length > 1 else 0
            else:
                width = asc_length + 0.5
        else:
            # Use Main Column length (column_height)
            if self.is_apron:
                width = self.column_height - 1 if self.column_height > 1 else 0
            else:
                width = self.column_height + 0.5
        
        if width <= 0:
            _logger.warning("Could not calculate valid width for Front Span covering")
            return
        
        # Round up to available width
        width = self._round_up_to_available_width(width)
        
        # Quantity = Width × Length × Nos (square meters)
        quantity = width * length * nos
        
        # Create component
        component_name = "Front Span Plastic Covering"
        size_spec = f"{width}m width"
        
        self._create_covering_component(
            'profiles',
            component_name,
            length,
            width,
            nos,
            quantity,
            size_spec
        )
        
        _logger.info(f"Created Front Span Covering: {nos} roll, {length:.2f}m × {width:.2f}m = {quantity:.2f} m²")
    
    def _calculate_back_span_covering(self):
        """Calculate Back Span Plastic covering"""
        if self.bay_length <= 0:
            _logger.warning("Insufficient data for Back Span covering calculation")
            return
        
        # Length = Bay Length + 1
        length = self.bay_length + 1
        
        # Nos = 1
        nos = 1
        
        # Width calculation based on ASC and Apron
        # Check if back span has ASC by checking width_back_span_coridoor
        if hasattr(self, 'width_back_span_coridoor') and self.width_back_span_coridoor > 0:
            asc_length = self._get_asc_length()
            if self.is_apron:
                width = asc_length - 1 if asc_length > 1 else 0
            else:
                width = asc_length + 0.5
        else:
            # Use Main Column length (column_height)
            if self.is_apron:
                width = self.column_height - 1 if self.column_height > 1 else 0
            else:
                width = self.column_height + 0.5
        
        if width <= 0:
            _logger.warning("Could not calculate valid width for Back Span covering")
            return
        
        # Round up to available width
        width = self._round_up_to_available_width(width)
        
        # Quantity = Width × Length × Nos (square meters)
        quantity = width * length * nos
        
        # Create component
        component_name = "Back Span Plastic Covering"
        size_spec = f"{width}m width"
        
        self._create_covering_component(
            'profiles',
            component_name,
            length,
            width,
            nos,
            quantity,
            size_spec
        )
        
        _logger.info(f"Created Back Span Covering: {nos} roll, {length:.2f}m × {width:.2f}m = {quantity:.2f} m²")
    
    def _calculate_front_bay_covering(self):
        """Calculate Front Bay Plastic covering"""
        if self.span_length <= 0:
            _logger.warning("Insufficient data for Front Bay covering calculation")
            return
        
        # Length = Span Length + 1
        length = self.span_length + 1
        
        # Nos = 1
        nos = 1
        
        # Width calculation based on ASC and Apron
        # Check if front bay has ASC by checking width_front_bay_coridoor
        if hasattr(self, 'width_front_bay_coridoor') and self.width_front_bay_coridoor > 0:
            asc_length = self._get_asc_length()
            if self.is_apron:
                width = asc_length - 1 if asc_length > 1 else 0
            else:
                width = asc_length + 0.5
        else:
            # Use Main Column length (column_height)
            if self.is_apron:
                width = self.column_height - 1 if self.column_height > 1 else 0
            else:
                width = self.column_height + 0.5
        
        if width <= 0:
            _logger.warning("Could not calculate valid width for Front Bay covering")
            return
        
        # Round up to available width
        width = self._round_up_to_available_width(width)
        
        # Quantity = Width × Length × Nos (square meters)
        quantity = width * length * nos
        
        # Create component
        component_name = "Front Bay Plastic Covering"
        size_spec = f"{width}m width"
        
        self._create_covering_component(
            'profiles',
            component_name,
            length,
            width,
            nos,
            quantity,
            size_spec
        )
        
        _logger.info(f"Created Front Bay Covering: {nos} roll, {length:.2f}m × {width:.2f}m = {quantity:.2f} m²")
    
    def _calculate_back_bay_covering(self):
        """Calculate Back Bay Plastic covering"""
        if self.span_length <= 0:
            _logger.warning("Insufficient data for Back Bay covering calculation")
            return
        
        # Length = Span Length + 1
        length = self.span_length + 1
        
        # Nos = 1
        nos = 1
        
        # Width calculation based on ASC and Apron
        # Check if back bay has ASC by checking width_back_bay_coridoor
        if hasattr(self, 'width_back_bay_coridoor') and self.width_back_bay_coridoor > 0:
            asc_length = self._get_asc_length()
            if self.is_apron:
                width = asc_length - 1 if asc_length > 1 else 0
            else:
                width = asc_length + 0.5
        else:
            # Use Main Column length (column_height)
            if self.is_apron:
                width = self.column_height - 1 if self.column_height > 1 else 0
            else:
                width = self.column_height + 0.5
        
        if width <= 0:
            _logger.warning("Could not calculate valid width for Back Bay covering")
            return
        
        # Round up to available width
        width = self._round_up_to_available_width(width)
        
        # Quantity = Width × Length × Nos (square meters)
        quantity = width * length * nos
        
        # Create component
        component_name = "Back Bay Plastic Covering"
        size_spec = f"{width}m width"
        
        self._create_covering_component(
            'profiles',
            component_name,
            length,
            width,
            nos,
            quantity,
            size_spec
        )
        
        _logger.info(f"Created Back Bay Covering: {nos} roll, {length:.2f}m × {width:.2f}m = {quantity:.2f} m²")
    
    def _calculate_gable_covering(self):
        """Calculate Front & Back Gable Plastic covering"""
        if self.bay_length <= 0 or self.top_ridge_height <= 0 or self.column_height <= 0:
            _logger.warning("Insufficient data for Gable covering calculation")
            return
        
        # Length = Bay Length + 1
        length = self.bay_length + 1
        
        # Nos = 2 (front and back)
        nos = 2
        
        # Width = (Top Ridge Height - Column Height + 0.5)
        width = self.top_ridge_height - self.column_height + 0.5
        
        if width <= 0:
            _logger.warning("Invalid width for Gable covering")
            return
        
        # Round up to available width
        width = self._round_up_to_available_width(width)
        
        # Quantity = Width × Length × Nos (square meters)
        quantity = width * length * nos
        
        # Create component
        component_name = "Front & Back Gable Plastic Covering"
        size_spec = f"{width}m width"
        
        self._create_covering_component(
            'profiles',
            component_name,
            length,
            width,
            nos,
            quantity,
            size_spec
        )
        
        _logger.info(f"Created Gable Covering: {nos} rolls, {length:.2f}m × {width:.2f}m = {quantity:.2f} m²")
    
    def _calculate_side_corridor_corner_covering(self):
        """Calculate Side Corridor Corner Plastic covering"""
        # Calculate number of corridors from ASC widths
        no_of_corridors = 0
        asc_width = 0
        
        if hasattr(self, 'width_front_span_coridoor') and self.width_front_span_coridoor > 0:
            no_of_corridors += 1
            asc_width = self.width_front_span_coridoor
        if hasattr(self, 'width_back_span_coridoor') and self.width_back_span_coridoor > 0:
            no_of_corridors += 1
            if asc_width == 0:
                asc_width = self.width_back_span_coridoor
        if hasattr(self, 'width_front_bay_coridoor') and self.width_front_bay_coridoor > 0:
            no_of_corridors += 1
            if asc_width == 0:
                asc_width = self.width_front_bay_coridoor
        if hasattr(self, 'width_back_bay_coridoor') and self.width_back_bay_coridoor > 0:
            no_of_corridors += 1
            if asc_width == 0:
                asc_width = self.width_back_bay_coridoor
        
        if no_of_corridors <= 0 or asc_width <= 0:
            _logger.info("Side Corridor Corner covering not applicable (no corridors or ASC width)")
            return
        
        # Length = sqrt((asc_width * asc_width)*2) + 1
        length = sqrt((asc_width * asc_width) * 2) + 1
        
        # Nos = (No of Corridors + 1) but maximum 4
        nos = min(no_of_corridors + 1, 4)
        
        # Width = ASC Pipe Length + 0.5
        asc_length = self._get_asc_length()
        width = asc_length + 0.5 if asc_length > 0 else 0
        
        if width <= 0:
            _logger.warning("Could not calculate valid width for Side Corridor Corner covering")
            return
        
        # Round up to available width
        width = self._round_up_to_available_width(width)
        
        # Quantity = Width × Length × Nos (square meters)
        quantity = width * length * nos
        
        # Create component
        component_name = "Side Corridor Corner Plastic Covering"
        size_spec = f"{width}m width"
        
        self._create_covering_component(
            'profiles',
            component_name,
            length,
            width,
            nos,
            quantity,
            size_spec
        )
        
        _logger.info(f"Created Side Corridor Corner Covering: {nos} rolls, {length:.2f}m × {width:.2f}m = {quantity:.2f} m²")
    
    def _calculate_entry_chambers_covering(self):
        """Calculate Entry Chambers Plastic covering"""
        # Get chamber count from doors module
        entry_chambers = 0
        if hasattr(self, 'entry_chambers_count'):
            entry_chambers = self.entry_chambers_count
        
        if entry_chambers <= 0:
            _logger.info("Entry Chambers covering not applicable (no chambers)")
            return
        
        # Length = 25
        length = 25.0
        
        # Nos = No of Chambers
        nos = entry_chambers
        
        # Width = 4.5
        width = 4.5
        
        # Quantity = Width × Length × Nos (square meters)
        quantity = width * length * nos
        
        # Create component
        component_name = "Entry Chambers Plastic Covering"
        size_spec = f"{width}m width"
        
        self._create_covering_component(
            'profiles',
            component_name,
            length,
            width,
            nos,
            quantity,
            size_spec
        )
        
        _logger.info(f"Created Entry Chambers Covering: {nos} rolls, {length:.2f}m × {width:.2f}m = {quantity:.2f} m²")
    
    def _calculate_apron_covering(self):
        """Calculate Apron Plastic covering"""
        if not self.is_apron:
            _logger.info("Apron covering not applicable (Apron disabled)")
            return
        
        if not self.apron_width_id:
            _logger.warning("Apron width not selected")
            return
        
        if self.span_length <= 0 or self.bay_length <= 0:
            _logger.warning("Insufficient data for Apron covering calculation")
            return
        
        # Length = ((Span Length + 1) + (Bay Length + 1)) * 2
        length = ((self.span_length + 1) + (self.bay_length + 1)) * 2
        
        # Nos = 1
        nos = 1
        
        # Width from selected master
        width = self.apron_width_id.width_value
        unit_price = self.apron_width_id.unit_price
        
        # Quantity = Width × Length × Nos (square meters)
        quantity = width * length * nos
        
        # Create component with custom price
        component_name = "Apron Plastic Covering"
        size_spec = f"{width}m width"
        
        self._create_covering_component_with_price(
            'profiles',
            component_name,
            length,
            width,
            nos,
            quantity,
            size_spec,
            unit_price
        )
        
        _logger.info(f"Created Apron Covering: {nos} roll, {length:.2f}m × {width:.2f}m = {quantity:.2f} m² @ ₹{unit_price}/m²")
    
    def _calculate_insect_net_covering(self):
        """Calculate Insect Net covering"""
        if not self.calculate_insect_net:
            _logger.info("Insect Net covering not applicable (disabled)")
            return
        
        if not self.insect_net_width_id:
            _logger.warning("Insect Net width not selected")
            return
        
        if self.span_length <= 0 or self.bay_length <= 0:
            _logger.warning("Insufficient data for Insect Net covering calculation")
            return
        
        # Length = ((Span Length + 1) + (Bay Length + 1)) * 2
        length = ((self.span_length + 1) + (self.bay_length + 1)) * 2
        
        # Nos = 1
        nos = 1
        
        # Width from selected master
        width = self.insect_net_width_id.width_value
        unit_price = self.insect_net_width_id.unit_price
        
        # Quantity = Width × Length × Nos (square meters)
        quantity = width * length * nos
        
        # Create component with custom price
        component_name = "Insect Net Covering"
        size_spec = f"{width}m width"
        
        self._create_covering_component_with_price(
            'profiles',
            component_name,
            length,
            width,
            nos,
            quantity,
            size_spec,
            unit_price
        )
        
        _logger.info(f"Created Insect Net Covering: {nos} roll, {length:.2f}m × {width:.2f}m = {quantity:.2f} m² @ ₹{unit_price}/m²")
    
    def _get_asc_length(self):
        """
        Get ASC length from ASC components
        Tries to find the length from ASC Pipes components
        """
        if not hasattr(self, 'asc_component_ids'):
            return 0
        
        # Try to get length from any ASC Pipes component
        asc_pipes = self.asc_component_ids.filtered(
            lambda c: 'ASC Pipes' in c.name or 'ASC Pipe' in c.name
        )
        
        if asc_pipes:
            # Return the length of the first ASC pipe found
            # This represents the diagonal length from column to ASC width
            return asc_pipes[0].length
        
        # Fallback: calculate from width_front_span_coridoor or width_front_bay_coridoor
        if hasattr(self, 'width_front_span_coridoor') and self.width_front_span_coridoor > 0:
            # Calculate diagonal: sqrt(width^2 + column_height^2)
            return sqrt(self.width_front_span_coridoor ** 2 + self.column_height ** 2)
        elif hasattr(self, 'width_front_bay_coridoor') and self.width_front_bay_coridoor > 0:
            return sqrt(self.width_front_bay_coridoor ** 2 + self.column_height ** 2)
        
        return 0
    
    def _round_up_to_available_width(self, required_width):
        """
        Round up required width to the nearest available covering width
        
        Args:
            required_width: The minimum width required
        
        Returns:
            The nearest available width that is >= required_width
        """
        # Get all active available widths
        available_widths = self.env['covering.width'].search([
            ('active', '=', True),
            ('width_value', '>=', required_width)
        ], order='width_value asc', limit=1)
        
        if available_widths:
            return available_widths[0].width_value
        
        # If no suitable width found, round up to nearest 0.5m
        return ceil(required_width * 2) / 2
    
    def _create_covering_component(self, section, name, length, width, rolls, quantity, size_spec):
        """
        Create covering component with length, width, rolls, and quantity
        
        Args:
            section: Component section ('profiles')
            name: Component name
            length: Length of each roll in meters
            width: Width of covering in meters
            rolls: Number of rolls
            quantity: Total square meters (width × length × rolls)
            size_spec: Size specification string
        """
        try:
            # Try to find matching master record
            master_record = self.env['accessories.master'].search([
                ('name', '=', name),
                ('category', '=', section),
                ('active', '=', True)
            ], limit=1)
            
            unit_price = master_record.unit_price if master_record else 0.0
            
            vals = {
                'green_master_id': self.id,
                'section': section,
                'name': name,
                'length': length,  # Length per roll
                'width': width,    # Width of covering
                'nos': rolls,      # Number of rolls
                'quantity': quantity,  # Total sq meters = width × length × rolls
                'size_specification': size_spec,
                'unit_price': unit_price,  # Price per square meter
                'is_calculated': True,
                'description': f"Auto-calculated covering: {rolls} rolls × {length:.2f}m × {width:.2f}m = {quantity:.2f} m²",
            }
            
            if master_record:
                vals['accessories_master_id'] = master_record.id
            
            component = self.env['accessories.component.line'].create(vals)
            
            _logger.info(f"Created covering component: {name} - {quantity:.2f} m² at {unit_price}/m²")
            return component
            
        except Exception as e:
            _logger.error(f"Error creating covering component {name}: {e}")
            return None
    
    def _create_covering_component_with_price(self, section, name, length, width, rolls, quantity, size_spec, unit_price):
        """
        Create covering component with specific unit price (for Apron and Insect Net)
        
        Args:
            section: Component section ('profiles')
            name: Component name
            length: Length of each roll in meters
            width: Width of covering in meters
            rolls: Number of rolls
            quantity: Total square meters (width × length × rolls)
            size_spec: Size specification string
            unit_price: Price per square meter (from width master)
        """
        try:
            vals = {
                'green_master_id': self.id,
                'section': section,
                'name': name,
                'length': length,  # Length per roll
                'width': width,    # Width of covering
                'nos': rolls,      # Number of rolls
                'quantity': quantity,  # Total sq meters = width × length × rolls
                'size_specification': size_spec,
                'unit_price': unit_price,  # Price per square meter from master
                'is_calculated': True,
                'description': f"Auto-calculated covering: {rolls} roll × {length:.2f}m × {width:.2f}m = {quantity:.2f} m² @ ₹{unit_price}/m²",
            }
            
            component = self.env['accessories.component.line'].create(vals)
            
            _logger.info(f"Created covering component: {name} - {quantity:.2f} m² at ₹{unit_price}/m²")
            return component
            
        except Exception as e:
            _logger.error(f"Error creating covering component {name}: {e}")
            return None
    
    @api.onchange('calculate_covering_material')
    def _onchange_calculate_covering_material(self):
        """Handle changes to covering material calculation flag"""
        if not self.calculate_covering_material:
            # Clear covering components when disabled
            return
    
    def action_calculate_covering(self):
        """Action to calculate only covering components"""
        for record in self:
            try:
                if not record.calculate_covering_material:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Covering Not Enabled',
                            'message': 'Please enable "Calculate Covering Material" first.',
                            'type': 'warning',
                        }
                    }
                
                # Clear existing covering components
                existing_covering = self.env['accessories.component.line'].search([
                    ('green_master_id', '=', record.id),
                    ('section', '=', 'profiles'),
                    ('name', 'ilike', 'Covering')
                ])
                if existing_covering:
                    existing_covering.unlink()
                
                # Calculate covering
                record._calculate_covering_components()
                
                component_count = len(record.covering_component_ids)
                total_cost = record.total_covering_cost
                
                message = f"COVERING CALCULATION COMPLETED:\n\n"
                message += f"Components generated: {component_count}\n"
                message += f"Total Covering Cost: {total_cost:.2f}\n\n"
                
                if record.is_apron:
                    message += "Configuration: With Apron\n"
                else:
                    message += "Configuration: Without Apron\n"
                
                asc_config = []
                if hasattr(record, 'width_front_span_coridoor') and record.width_front_span_coridoor > 0:
                    asc_config.append(f"Front Span ASC ({record.width_front_span_coridoor}m)")
                if hasattr(record, 'width_back_span_coridoor') and record.width_back_span_coridoor > 0:
                    asc_config.append(f"Back Span ASC ({record.width_back_span_coridoor}m)")
                if hasattr(record, 'width_front_bay_coridoor') and record.width_front_bay_coridoor > 0:
                    asc_config.append(f"Front Bay ASC ({record.width_front_bay_coridoor}m)")
                if hasattr(record, 'width_back_bay_coridoor') and record.width_back_bay_coridoor > 0:
                    asc_config.append(f"Back Bay ASC ({record.width_back_bay_coridoor}m)")
                
                if asc_config:
                    message += f"ASC: {', '.join(asc_config)}"
                else:
                    message += "ASC: None"
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Covering Calculated Successfully',
                        'message': message,
                        'type': 'success',
                        'sticky': True,
                    }
                }
            except Exception as e:
                _logger.error(f"Error in covering calculation: {e}")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Covering Calculation Error',
                        'message': f'Error occurred: {str(e)}',
                        'type': 'danger',
                    }
                }