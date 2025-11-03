from odoo import models, fields, api

class BankReconciliation(models.Model):
    _name = 'drkds.bank.reconciliation'
    _description = 'Bank Reconciliation'
    
    name = fields.Char('Name', required=True)
    journal_id = fields.Many2one('account.journal', 'Bank Journal', required=True)
    date = fields.Date('Date', required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    state = fields.Selection([('draft', 'Draft'), ('reconciled', 'Reconciled')], default='draft')
    statement_balance = fields.Monetary('Statement Balance')
    book_balance = fields.Monetary('Book Balance')
    difference = fields.Monetary('Difference', compute='_compute_difference', store=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    
    @api.depends('statement_balance', 'book_balance')
    def _compute_difference(self):
        for rec in self:
            rec.difference = rec.statement_balance - rec.book_balance
