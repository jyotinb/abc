from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    asset_id = fields.Many2one('drkds.asset', 'Asset')
    recurring_entry_id = fields.Many2one('drkds.recurring.entry', 'Recurring Entry', readonly=True)
