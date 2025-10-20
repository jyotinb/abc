from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class PackagingWizard(models.TransientModel):
    _name = 'packaging.wizard'
    _description = 'Packaging Wizard'

    package_type_id = fields.Many2one('product.packaging', string='Package Type', required=True, domain="[('product_id', '=', product_id)]")
    package_qty = fields.Float(string='Quantity to Pack', required=True)
    production_id = fields.Many2one('mrp.production', string='Manufacturing Order', required=True)
    product_id = fields.Many2one('product.product', related='production_id.product_id', string='Product', store=True, readonly=True)

    @api.onchange('production_id')
    def _onchange_production_id(self):
        if self.production_id:
            self.product_id = self.production_id.product_id.id

    @api.model
    def create(self, vals):
        if vals.get('production_id') and not vals.get('product_id'):
            production = self.env['mrp.production'].browse(vals['production_id'])
            vals['product_id'] = production.product_id.id
        return super(PackagingWizard, self).create(vals)

    def apply_packaging(self):
        self.ensure_one()
        self.production_id.create_packages(self.package_type_id.id, self.package_qty)

        # Get the quant for the current product and location
        quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product_id.id),
            ('location_id', '=', self.production_id.location_src_id.id)
        ], limit=1)

        if quant:
            quant.sudo().write({
                'quantity': quant.quantity - self.package_qty  # Adjust the quantity
            })
        else:
            self.env['stock.quant'].create({
                'product_id': self.product_id.id,
                'location_id': self.production_id.location_src_id.id,
                'quantity': -self.package_qty  # Set the initial quantity
            })

        # Explicitly unlink the wizard record to avoid foreign key issues
        self.unlink()


        
    def unlink(self):
        _logger.info("Unlinking record: %s", self.ids)
        return super(PackagingWizard, self).unlink()
