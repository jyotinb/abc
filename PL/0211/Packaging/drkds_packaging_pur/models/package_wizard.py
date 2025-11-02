from odoo import models, fields, api
from odoo.exceptions import UserError  # Import UserError

class PackageCreationWizard(models.TransientModel):
    _name = 'package.creation.wizard'
    _description = 'Package Creation Wizard'

    picking_id = fields.Many2one('stock.picking', string='Picking', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    packaging_id = fields.Many2one('product.packaging', string='Packaging Type', required=True)
    package_qty = fields.Float(string='Quantity to Pack', required=True)
    product_ids = fields.Many2many('product.product', string='Products in Picking', compute='_compute_product_ids')
    quantity_available = fields.Float(string='Order Quantity', compute='_compute_quantity_available', store=True)
    
    
    
    packaging_with_qty_id = fields.Many2one('product.packaging', string='Packaging Type', required=True)
    packaging_description = fields.Char(compute='_compute_packaging_description', string='Packaging Description')
    packaging_ids = fields.Many2many('product.packaging', compute='_compute_packaging_ids')

    @api.depends('product_id')
    def _compute_packaging_ids(self):
        for wizard in self:
            if wizard.product_id:
                wizard.packaging_ids = self.env['product.packaging'].search([('product_id', '=', wizard.product_id.id)])
            else:
                wizard.packaging_ids = False

    @api.depends('packaging_with_qty_id')
    def _compute_packaging_description(self):
        for wizard in self:
            if wizard.packaging_with_qty_id:
                wizard.packaging_description = f"{wizard.packaging_with_qty_id.name} - {wizard.packaging_with_qty_id.qty} "
            else:
                wizard.packaging_description = ""
                
    @api.onchange('packaging_with_qty_id')
    def _onchange_packaging_with_qty_id(self):
        if self.packaging_with_qty_id:
            self.packaging_id = self.packaging_with_qty_id
        
        
    
    
    
    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        if self.picking_id:
            self.product_ids = self.picking_id.move_line_ids.mapped('product_id')
        else:
            self.product_ids = False

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            return {'domain': {'packaging_id': [('product_id', '=', self.product_id.id)]}}
            
    @api.depends('picking_id', 'product_id') 
    def _compute_quantity_available(self): 
        for wizard in self: 
            if wizard.picking_id and wizard.product_id: 
                move_lines = wizard.picking_id.move_line_ids.filtered(lambda m: m.product_id == wizard.product_id) 
                wizard.quantity_available = sum(move_lines.mapped('quantity')) 
            else: 
                wizard.quantity_available = 0

    def create_packages(self):
        """
        Create packages for the selected picking without validating the picking.
        """
        self.ensure_one()
        picking = self.picking_id
        product = self.product_id
        packaging = self.packaging_id
        qty_per_package = packaging.qty

        package_qty = self.package_qty
        package_count = int(package_qty / qty_per_package)

        if picking.state == 'done':
            raise UserError(
                f"Cannot create packages for a completed picking: {picking.name}. "
                f"Ensure packaging is done before completing the picking."
            )

        # Filter move lines to only include those relevant for packaging
        move_lines = picking.move_line_ids.filtered(
            lambda m: m.product_id == product and m.state in ('confirmed', 'assigned')
        )

        if not move_lines:
            raise UserError(
                f"No available move lines for the selected product.\n"
                f"Product: {product.display_name}\n"
                f"Picking: {picking.name}\n"
                f"States: {[m.state for m in picking.move_line_ids]}"
            )

        # Create packages without validation
        for _ in range(package_count):
            sequence_number = self.env['ir.sequence'].next_by_code('stock.package')
            package_name = f'{packaging.name}-{sequence_number}'  # Combine packaging name with sequence

            package = self.env['stock.quant.package'].create({
                'name': package_name,
                'packaging_id': packaging.id,
                'package_type_id': packaging.package_type_id.id,
            })
            self.env['stock.move.line'].create({
                'move_id': move_lines.move_id.id,
                'product_id': product.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                'product_uom_id': product.uom_id.id,
                'quantity': qty_per_package,  # Correct field name
                'result_package_id': package.id,
                'picking_id': picking.id
            })

        if package_qty % qty_per_package:
            sequence_number = self.env['ir.sequence'].next_by_code('stock.package')
            package_name = f'{packaging.name}-{sequence_number}'  # Combine packaging name with sequence
            package = self.env['stock.quant.package'].create({
                'name': package_name,
                'packaging_id': packaging.id,
                'package_type_id': packaging.package_type_id.id
            })
            self.env['stock.move.line'].create({
                'move_id': move_lines.move_id.id,
                'product_id': product.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                'product_uom_id': product.uom_id.id,
                'quantity': package_qty % qty_per_package,  # Correct field name
                'result_package_id': package.id,
                'picking_id': picking.id
            })

    
    def update_unpacked_qty(self):
        """
        Update unpacked quantities to reflect:
        unpacked_qty = unpacked_qty - packed_qty
        """
        for picking in self:
            for move in picking.move_lines:
                # Calculate the total packed quantity for this move
                packed_qty = sum(move.move_line_ids.filtered(lambda line: line.result_package_id).mapped('quantity'))
                
                # Filter unpacked lines (lines without packages)
                unpacked_lines = move.move_line_ids.filtered(lambda line: not line.result_package_id)
                
                for line in unpacked_lines:
                    # Update the unpacked quantity
                    if line.quantity > packed_qty:
                        line.quantity -= packed_qty
                    else:
                        line.quantity = 0  # Prevent negative values
                        packed_qty -= line.quantity
                
                # Ensure no unpacked line remains with excess quantity
                if packed_qty > 0:
                    raise UserError(f"Packed quantity exceeds the unpacked quantity for product: {move.product_id.display_name}.")
                
                
                
    def action_validate(self):
        """
        Update unpacked quantities before validating the picking.
        """
        raise UserError(f"Packed quantity quantity" )
        self.update_unpacked_qty()  # Call the method to update unpacked quantities
        return super(StockPicking, self).action_validate()  # Proceed with validation
        
        
class QuantPackage(models.Model):
    _inherit = "stock.quant.package"
    
    actual_gross_weight = fields.Float(string="Actual Gross Weight")