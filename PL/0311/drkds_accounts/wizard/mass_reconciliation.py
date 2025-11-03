from odoo import models, fields

class MassReconciliationWizard(models.TransientModel):
    _name = 'drkds.mass.reconciliation.wizard'
    _description = 'Mass Reconciliation'
    
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    account_ids = fields.Many2many('account.account', string='Accounts', required=True)
    date_from = fields.Date('From Date')
    date_to = fields.Date('To Date')
    
    def action_reconcile(self):
        return {'type': 'ir.actions.act_window_close'}
