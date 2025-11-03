from odoo import models, fields

class AssetReportWizard(models.TransientModel):
    _name = 'drkds.asset.report.wizard'
    _description = 'Asset Report'
    
    date_from = fields.Date('From Date', required=True)
    date_to = fields.Date('To Date', required=True)
    category_ids = fields.Many2many('drkds.asset.category', string='Categories')
    
    def print_report(self):
        return {'type': 'ir.actions.act_window_close'}
