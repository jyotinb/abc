from odoo import models, fields

class FiscalYearCloseWizard(models.TransientModel):
    _name = 'drkds.fiscal.year.close.wizard'
    _description = 'Fiscal Year Closing'
    
    fiscal_year_id = fields.Many2one('drkds.fiscal.year', 'Fiscal Year', required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    closing_date = fields.Date('Closing Date', required=True)
    
    def action_close_fiscal_year(self):
        return {'type': 'ir.actions.act_window_close'}
