from odoo import models, fields

class AnalyticReportWizard(models.TransientModel):
    _name = 'drkds.analytic.report.wizard'
    _description = 'Analytic Report'
    
    date_from = fields.Date('From Date', required=True, default=lambda self: fields.Date.today().replace(day=1))
    date_to = fields.Date('To Date', required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    analytic_account_ids = fields.Many2many('account.analytic.account', string='Analytic Accounts')
    
    def print_report(self):
        return {'type': 'ir.actions.act_window_close'}
