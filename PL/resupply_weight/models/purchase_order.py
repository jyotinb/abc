# -*- coding: utf-8 -*-
from odoo import models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_view_subcontracting_resupply(self):
        return self.with_context(resupply=True)._get_action_view_picking(self._get_subcontracting_resupplies())

    def _get_action_view_picking(self, pickings):
        res = super()._get_action_view_picking(pickings)
        if not self.env.context.get('resupply'):
            res['context'].update({'is_receipt': True})
        return res
