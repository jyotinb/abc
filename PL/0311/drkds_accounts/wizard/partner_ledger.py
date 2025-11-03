from odoo import models, fields

class PartnerLedgerWizard(models.TransientModel):
    _name = 'drkds.partner.ledger.wizard'
    _description = 'Partner Ledger Report'
    
    date_from = fields.Date('From Date', required=True, default=lambda self: fields.Date.today().replace(day=1))
    date_to = fields.Date('To Date', required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    partner_ids = fields.Many2many('res.partner', string='Partners')
    result_selection = fields.Selection([
        ('customer', 'Receivable Accounts'),
        ('supplier', 'Payable Accounts'),
        ('customer_supplier', 'Receivable and Payable Accounts')
    ], string='Partner Type', default='customer', required=True)
    
    def print_report(self):
        return {'type': 'ir.actions.act_window_close'}
