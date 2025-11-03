from odoo import models, fields, api

class AnalyticDistribution(models.Model):
    _name = 'drkds.analytic.distribution'
    _description = 'Analytic Distribution Template'
    
    name = fields.Char('Name', required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'
    
    budget_ids = fields.One2many('drkds.budget', 'analytic_account_id', 'Budgets')
    budget_count = fields.Integer('Budget Count', compute='_compute_budget_count')
    
    @api.depends('budget_ids')
    def _compute_budget_count(self):
        for account in self:
            account.budget_count = len(account.budget_ids)
