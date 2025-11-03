from odoo import models, fields, api

class AccountingDashboard(models.Model):
    _name = 'drkds.dashboard'
    _description = 'Accounting Dashboard'
    
    name = fields.Char('Dashboard', default='Accounting Dashboard')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    total_receivable = fields.Monetary('Total Receivable', compute='_compute_kpis')
    total_payable = fields.Monetary('Total Payable', compute='_compute_kpis')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    
    def _compute_kpis(self):
        for rec in self:
            rec.total_receivable = 0.0
            rec.total_payable = 0.0
