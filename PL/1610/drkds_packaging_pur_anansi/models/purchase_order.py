from odoo import models, fields

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    package_qty = fields.Float(string='Package Quantity', required=True, default=1)
    package_type_id = fields.Many2one('product.packaging', string='Package Type')

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    package_qty = fields.Float(string='Package Quantity', related='order_id.package_qty', readonly=False)
    package_type_id = fields.Many2one('product.packaging', related='order_id.package_type_id', readonly=False)
