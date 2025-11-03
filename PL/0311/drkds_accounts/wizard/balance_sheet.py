from odoo import models, fields

class BalanceSheetWizard(models.TransientModel):
    _name = 'drkds.balance.sheet.wizard'
    _description = 'Balance Sheet Report'
    
    date = fields.Date('As of Date', required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    target_move = fields.Selection([('posted', 'Posted'), ('all', 'All')], default='posted', required=True)
    
    def print_report(self):
        return {'type': 'ir.actions.act_window_close'}
