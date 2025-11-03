from odoo import models, fields

class CashFlowWizard(models.TransientModel):
    _name = 'drkds.cash.flow.wizard'
    _description = 'Cash Flow Statement'
    
    date_from = fields.Date('From Date', required=True, default=lambda self: fields.Date.today().replace(day=1))
    date_to = fields.Date('To Date', required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    method = fields.Selection([('direct', 'Direct Method'), ('indirect', 'Indirect Method')], default='indirect')
    
    def print_report(self):
        return {'type': 'ir.actions.act_window_close'}
