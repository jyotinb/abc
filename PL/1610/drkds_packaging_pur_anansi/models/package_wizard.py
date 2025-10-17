import logging
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)

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
            picking = self.picking_id
            move = picking.move_ids.filtered(lambda m: m.product_id == self.product_id  and m.product_packaging_id == self.packaging_with_qty_id)
            move_lines = picking.move_line_ids.filtered(lambda m: m.product_id == self.product_id  and m.move_id in move and m.quantity> 0 and m.state in ('confirmed', 'assigned', 'partially_available') and not m.result_package_id)
            if move_lines:
                self.package_qty = sum(move_lines.mapped('quantity'))
            else:
                self.package_qty = 0        
    
    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        if self.picking_id:
            self.product_ids = self.picking_id.move_line_ids.filtered(lambda m: m.state in ('confirmed', 'assigned', 'partially_available') and not m.result_package_id and m.quantity> 0).mapped('product_id')
        else:
            self.product_ids = False

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            picking = self.picking_id
            if picking:
                move_lines = picking.move_line_ids.filtered(lambda m: m.product_id == self.product_id and m.quantity> 0 and m.state in ('confirmed', 'assigned', 'partially_available') and not m.result_package_id)
                print(f"Move lines: {move_lines}")
                if move_lines:
                    self.package_qty = sum(move_lines.mapped('quantity'))
                else:
                    self.package_qty = 0
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
        packaging = self.packaging_with_qty_id
        qty_per_package = packaging.qty

        if qty_per_package <= 0:
            raise UserError("Packaging quantity must be positive.")
        # Total units to pack
        if qty_per_package > self.package_qty:
            total_qty_to_pack = 1
            qty_per_package = self.package_qty
        else:
            total_qty_to_pack = int(self.package_qty / qty_per_package)# Total units to pack
        if picking.state == 'done':
            raise UserError(
                f"Cannot create packages for a completed picking: {picking.name}. "
                f"Ensure packaging is done before completing the picking."
            )
        # Filter move lines to only include those relevant for packaging
        move_lines = picking.move_line_ids.filtered(
            lambda m: m.product_id == product and m.state in ('confirmed', 'assigned', 'partially_available')
        )
        if not move_lines:
            raise UserError(
                f"No available move lines for the selected product.\n"
                f"Product: {product.display_name}\n"
                f"Picking: {picking.name}\n"
                f"States: {[m.state for m in picking.move_line_ids]}"
            )
       
        # Create full packages
        for _ in range(total_qty_to_pack):
            product_moves = picking.move_ids.filtered(lambda m: m.product_id == product and m.product_packaging_id == packaging) 
           
            if not product_moves:
                raise UserError(f"No moves found for product {product.display_name} in picking {picking.name}")
            
            main_move = next((
                    move for move in product_moves
                    if move.move_line_ids.filtered(lambda ml: not ml.result_package_id and ml.quantity > 0)
                ), False)
            if not main_move:
                raise UserError(f"All moves for {product.display_name} in picking {picking.name} are already packed or have 0 quantity.")

            sequence_number = self.env['ir.sequence'].next_by_code('stock.package')
            package_name = f'{packaging.name}-{sequence_number}'
            package = self.env['stock.quant.package'].create({
                'name': package_name,
                'packaging_id': packaging.id,
                'package_type_id': packaging.package_type_id.id,
            })
            self.env['stock.move.line'].create({
                'move_id': main_move.id,
                'product_id': product.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                'product_uom_id': product.uom_id.id,
                'quantity': qty_per_package,
                'result_package_id': package.id,
                'picking_id': picking.id
            })
            main_line = picking.move_line_ids.filtered(lambda ml: ml.product_id == product and ml.move_id == main_move and not ml.result_package_id and ml.quantity > 0)[:1]
            if main_line:
                remaining_qty = main_line.quantity - qty_per_package
                main_line.sudo().write({'quantity': remaining_qty})


        # Force UI refresh by triggering a recomputation
        try:
            picking.message_post(body="Package created", message_type="notification")
        except:
            pass

    def update_main_quantity(self, product, picking):
        """Update main move line quantity by subtracting packaged amounts"""
        _logger.info(f"=== UPDATE_MAIN_QUANTITY DEBUG ===")
        _logger.info(f"Product: {product.name}")
        _logger.info(f"Picking: {picking.name}")
        
        # Get all move lines for this product
        all_lines = picking.move_line_ids.filtered(lambda ml: ml.product_id == product)
        _logger.info(f"All lines found: {len(all_lines)}")
        
        for line in all_lines:
            _logger.info(f"  Line ID {line.id}: qty={line.quantity}, package={line.result_package_id.name if line.result_package_id else 'None'}")
        
        # Separate packaged and main lines
        packaged_lines = all_lines.filtered(lambda ml: ml.result_package_id)
        main_lines = all_lines.filtered(lambda ml: not ml.result_package_id)
        
        _logger.info(f"Packaged lines: {len(packaged_lines)}")
        _logger.info(f"Main lines: {len(main_lines)}")
        
        # Calculate total packaged quantity - FIXED LOGIC
        # IMPORTANT: The quantity on packaged lines already represents the total items packed
        total_items_packaged = sum(packaged_lines.mapped('quantity'))
        
        _logger.info(f"Total items packed: {total_items_packaged}")
        
        # Update main line quantity if found
        if main_lines and len(main_lines) == 1:
            main_line = main_lines[0]
            original_demand = main_line.move_id.product_uom_qty
            current_qty = main_line.quantity
            
            _logger.info(f"Main line original demand: {original_demand}")
            _logger.info(f"Main line current quantity: {current_qty}")
            
            # The correct calculation
            remaining_qty = original_demand - total_items_packaged
            
            _logger.info(f"Calculated remaining: {original_demand} - {total_items_packaged} = {remaining_qty}")
            
            # Ensure non-negative
            if remaining_qty < 0:
                remaining_qty = 0
                _logger.info(f"Adjusted to 0 (was negative)")
            
            # Update quantity if there's a meaningful change
            if abs(remaining_qty - current_qty) > 0.001:
                _logger.info(f"🔧 Updating main line quantity from {current_qty} to {remaining_qty}")
                main_line.sudo().write({'quantity': remaining_qty})
                
                # DO NOT update stock.move.product_uom_qty - this causes status changes and deletions
                # Only update the move line quantity - this is safe
                _logger.info(f"✅ Move line updated successfully - DO NOT update stock.move.product_uom_qty")
                _logger.info(f"✅ Update completed")
            else:
                _logger.info(f"No update needed: {current_qty} ≈ {remaining_qty} (difference < 0.001)")
        else:
            _logger.warning(f"❌ Could not find single main line. Found: {[l.id for l in main_lines]}")
        
        _logger.info(f"=== END DEBUG ===")

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
        # This method is not being used correctly - removing the broken line
        # self.update_unpacked_qty()  # Call the method to update unpacked quantities
        return super().action_validate()  # Proceed with validation
        
        
class QuantPackage(models.Model):
    _inherit = "stock.quant.package"
    
    actual_gross_weight = fields.Float(string="Actual Gross Weight")