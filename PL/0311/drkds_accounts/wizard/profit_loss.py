from odoo import models, fields

class ProfitLossWizard(models.TransientModel):
    _name = 'drkds.profit.loss.wizard'
    _description = 'Profit & Loss Report'
    
    date_from = fields.Date('From Date', required=True, default=lambda self: fields.Date.today().replace(day=1))
    date_to = fields.Date('To Date', required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    target_move = fields.Selection([('posted', 'Posted'), ('all', 'All')], default='posted', required=True)
    
    def print_report(self):
        return {'type': 'ir.actions.act_window_close'}
