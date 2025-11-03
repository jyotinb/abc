from odoo import models, fields

class InvoiceAnalysisWizard(models.TransientModel):
    _name = 'drkds.invoice.analysis.wizard'
    _description = 'Invoice Analysis Report'
    
    date_from = fields.Date('From Date', required=True, default=lambda self: fields.Date.today().replace(day=1))
    date_to = fields.Date('To Date', required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    report_type = fields.Selection([
        ('aging', 'Aging Analysis'),
        ('dso', 'DSO Analysis'),
    ], required=True, default='aging')
    
    def print_report(self):
        return {'type': 'ir.actions.act_window_close'}
