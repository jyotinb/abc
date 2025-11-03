from odoo import models, fields

class AgedPartnerWizard(models.TransientModel):
    _name = 'drkds.aged.partner.wizard'
    _description = 'Aged Partner Balance'
    
    date = fields.Date('As of Date', required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    result_selection = fields.Selection([
        ('customer', 'Receivable'),
        ('supplier', 'Payable'),
    ], string='Type', default='customer', required=True)
    partner_ids = fields.Many2many('res.partner', string='Partners')
    
    def print_report(self):
        return {'type': 'ir.actions.act_window_close'}
