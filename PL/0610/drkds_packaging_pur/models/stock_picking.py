from odoo import models, fields, api
from odoo.exceptions import UserError

class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    packaging_id = fields.Many2one('product.packaging', string='Packaging Type')
    package_type_id = fields.Many2one('stock.package.type', string='Package Type')

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    package_count = fields.Integer(string='Package Count', compute='_compute_package_count')

    @api.model
    def create(self, vals_list):
        pickings = super(StockPicking, self).create(vals_list)
        for picking in pickings:
            if picking.picking_type_id.code == 'incoming' and picking.purchase_id:
                picking._create_packages_for_receipt()
        return pickings

    def _compute_package_count(self):
        for picking in self:
            picking.package_count = len(picking.move_line_ids.mapped('result_package_id'))

    def action_view_packages(self):
        action = self.env.ref('stock.action_package_view').read()[0]
        packages = self.move_line_ids.mapped('result_package_id')
        if len(packages) > 1:
            action['domain'] = [('id', 'in', packages.ids)]
        elif packages:
            action['views'] = [(self.env.ref('stock.view_picking_pack_operation_tree').id, 'tree'),
                               (self.env.ref('stock.view_package_form').id, 'form')]
            action['res_id'] = packages.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_create_packages_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'package.creation.wizard',
            'view_mode': 'form',
            'context': {'default_picking_id': self.id},
            'target': 'new'
        }

    # def update_unpacked_qty(self):
        # """
        # Update unpacked quantities to reflect total quantity as per demand:
        # packed_qty + unpacked_qty = demand_qty
        # """
        # for picking in self:
            # for move in picking.move_lines:
                # # Calculate the total packed quantity for this move
                # packed_qty = sum(move.move_line_ids.mapped('qty_done'))
                # demand_qty = move.product_uom_qty  # The demand quantity (total qty for move)

                # # The remaining unpacked quantity
                # unpacked_qty = demand_qty - packed_qty

                # # If there are unpacked lines, update them
                # unpacked_lines = move.move_line_ids.filtered(lambda line: not line.result_package_id)
                # if unpacked_lines:
                    # unpacked_line = unpacked_lines[0]
                    # unpacked_line.qty_done = unpacked_qty
                # else:
                    # # If no unpacked line exists, create a new one
                    # self.env['stock.move.line'].create({
                        # 'move_id': move.id,
                        # 'product_id': move.product_id.id,
                        # 'location_id': picking.location_id.id,
                        # 'location_dest_id': picking.location_dest_id.id,
                        # 'product_uom_id': move.product_uom.id,
                        # 'qty_done': unpacked_qty,
                        # 'picking_id': picking.id,
                    # })

                # # Ensure packed and unpacked quantities do not exceed demand
                # if packed_qty + unpacked_qty > demand_qty:
                    # raise UserError(f"Packed and unpacked quantities exceed demand for product: {move.product_id.display_name}.")

    # def create_packages(self):
        # """
        # Create packages for the selected picking without validating the picking.
        # """
        # self.ensure_one()
        # picking = self.picking_id
        # product = self.product_id
        # packaging = self.packaging_id
        # qty_per_package = packaging.qty
        # package_qty = self.package_qty
        # package_count = int(package_qty / qty_per_package)

        # # Filter to ensure only products in receipt operation lines are considered
        # move_lines = picking.move_line_ids.filtered(
            # lambda m: m.product_id == product and m.state in ('confirmed', 'assigned')
        # )

        # if not move_lines:
            # raise UserError(f"No available move lines for the selected product. Product: {product.display_name}, Picking: {picking.name}")

        # # Prevent validation safeguard
        # if picking.state == 'done':
            # raise UserError("Picking is already validated. Packages cannot be created for validated pickings.")

        # # Create packages without validating
        # for _ in range(package_count):
            # package = self.env['stock.quant.package'].create({
                # 'packaging_id': packaging.id
            # })
            # self.env['stock.move.line'].create({
                # 'move_id': move_lines.move_id.id,
                # 'product_id': product.id,
                # 'location_id': picking.location_id.id,
                # 'location_dest_id': picking.location_dest_id.id,
                # 'product_uom_id': product.uom_id.id,
                # 'qty_done': qty_per_package,
                # 'result_package_id': package.id,
                # 'picking_id': picking.id
            # })

        # # Handle remaining quantity if not evenly divisible
        # if package_qty % qty_per_package:
            # package = self.env['stock.quant.package'].create({
                # 'packaging_id': packaging.id
            # })
            # self.env['stock.move.line'].create({
                # 'move_id': move_lines.move_id.id,
                # 'product_id': product.id,
                # 'location_id': picking.location_id.id,
                # 'location_dest_id': picking.location_dest_id.id,
                # 'product_uom_id': product.uom_id.id,
                # 'qty_done': package_qty % qty_per_package,
                # 'result_package_id': package.id,
                # 'picking_id': picking.id
            # })

        # # Explicitly skip validation
        # picking.state = 'assigned'  # Ensure the picking remains in an intermediate state


 