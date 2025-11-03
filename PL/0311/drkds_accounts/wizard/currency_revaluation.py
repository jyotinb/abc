from odoo import models, fields

class CurrencyRevaluationWizard(models.TransientModel):
    _name = 'drkds.currency.revaluation.wizard'
    _description = 'Currency Revaluation'
    
    date = fields.Date('Revaluation Date', required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    journal_id = fields.Many2one('account.journal', 'Journal', required=True)
    
    def action_revaluate(self):
        return {'type': 'ir.actions.act_window_close'}
