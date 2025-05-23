from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    def action_open_export_wizard(self):
        """Open the export wizard for delivery orders"""
        self.ensure_one()
        if self.state != 'done':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Only completed delivery orders can be exported.',
                    'type': 'warning',
                    'sticky': False,
                }
            }
            
        return {
            'name': 'Export Delivery Order to Tally',
            'type': 'ir.actions.act_window',
            'res_model': 'export.delivery.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
            },
        }
