from odoo import models, fields, api
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    package_prefix = fields.Char(string='Package Prefix')
    gross_weight = fields.Float(
        string="Gross Weight", compute="_compute_gross_weight", store=True
    )
    net_weight = fields.Float(
        string="Net Weight", compute="_compute_gross_weight", store=True
    )
    packing_type = fields.Char(string="Packing Type") 

    def action_create_packages(self):
        self.ensure_one()
        if not self.package_prefix:
            raise UserError('Package Prefix is required.')
        package_number = 1
        for move_line in self.move_line_ids:
            product = move_line.product_id
            if product.packaging_ids:
                for packaging in product.packaging_ids:
                    package_qty = packaging.qty
                    total_qty = move_line.qty_done

                    num_packages = total_qty // package_qty
                    remainder_qty = total_qty % package_qty

                    for _ in range(int(num_packages)):
                        package_name = f"{self.package_prefix}{package_number:05d}"
                        package = self.env['stock.quant.package'].create({
                            'name': package_name,
                            'package_type_id': packaging.id,
                        })
                        package_number += 1
                        self.env['stock.quant'].create({
                            'product_id': product.id,
                            'quantity': package_qty,
                            'package_id': package.id,
                            'location_id': move_line.location_dest_id.id,
                        })

                    if remainder_qty > 0:
                        move_line.qty_done = remainder_qty
                    else:
                        move_line.unlink()
                        
    @api.depends('move_line_ids', 'move_line_ids.result_package_id','move_line_ids.result_package_id.shipping_weight' , 'move_line_ids.loose_item_weight') #
    def _compute_gross_weight(self):
        for picking in self:
            # Calculate the weight of packages
            package_weight = sum(
                package.shipping_weight or 0
                for package in picking.move_line_ids.mapped('result_package_id')
            )
            package_net_weight = sum(
                ((package.shipping_weight or 0) - (package.package_type_id.base_weight or 0))
                for package in picking.move_line_ids.mapped('result_package_id')
            )

            # Sum loose_item_weight field for all unpacked items
            loose_item_weight = sum(
                line.loose_item_weight
                for line in picking.move_line_ids
                if not line.result_package_id
            )

            # Total gross weight
            picking.gross_weight = package_weight + loose_item_weight
            
            
        
            
            
            
    # loose_item_weights_by_product = fields.Text(
        # string="Loose Item Weights by Product",
        # compute='_compute_loose_item_weights_by_product',
        # help="Aggregated loose item weights for each product"
    # )

    # @api.depends('move_line_ids.product_id', 'move_line_ids.loose_item_weight', 'move_line_ids.result_package_id')
    # def _compute_loose_item_weights_by_product(self):
        # for picking in self:
            # weights = {}
            # for line in picking.move_line_ids:
                # if not line.result_package_id:  # Only consider unpacked items
                    # product = line.product_id
                    # if product in weights:
                        # weights[product] += line.loose_item_weight
                    # else:
                        # weights[product] = line.loose_item_weight
            # # Store the result as a string representation of the dictionary
            # picking.loose_item_weights_by_product = str(weights)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    loose_item_weight = fields.Float(string='Loose Item Weight')





class StockPicking(models.Model):
    _inherit = 'stock.quant.package'

    @api.model
    def create(self, vals):
        # Generate custom pack code
        if 'name' not in vals or not vals['name']:
            last_package = self.search([], order='id desc', limit=1)
            last_number = 0
            if last_package and last_package.name.startswith('pack-'):
                try:
                    last_number = int(last_package.name.split('-')[1])
                except ValueError:
                    pass
            # Increment and format the number
            new_number = last_number + 1
            vals['name'] = f"Pack-{new_number:05}"
        return super(StockPicking, self).create(vals)


