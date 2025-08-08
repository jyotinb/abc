# -*- coding: utf-8 -*-
from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    delivered_weight = fields.Float(string='Delivered Weight')
    delivered_weight_uom_id = fields.Many2one('uom.uom', string='Delivered Weight Uom', domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)])
    received_weight = fields.Float(string='Received Weight')
    received_weight_uom_id = fields.Many2one('uom.uom', string='Received Weight Uom', domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)])
