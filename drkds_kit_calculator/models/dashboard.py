# File: drkds_kit_calculator/models/dashboard.py

from odoo import models, fields, api, _

class KitDashboard(models.TransientModel):
    _name = 'kit.dashboard'
    _description = 'Kit Calculator Dashboard'
    
    # Statistics
    total_cost_sheets = fields.Integer(string='Total Cost Sheets', compute='_compute_stats')
    confirmed_sheets = fields.Integer(string='Confirmed Sheets', compute='_compute_stats')
    total_components = fields.Integer(string='Total Components', compute='_compute_stats')
    total_templates = fields.Integer(string='Total Templates', compute='_compute_stats')
    
    # Financial
    total_value = fields.Float(string='Total Value', compute='_compute_financial')
    average_value = fields.Float(string='Average Value', compute='_compute_financial')
    
    @api.depends_context('uid')
    def _compute_stats(self):
        for record in self:
            record.total_cost_sheets = self.env['kit.cost.sheet'].search_count([])
            record.confirmed_sheets = self.env['kit.cost.sheet'].search_count([('state', '=', 'confirmed')])
            record.total_components = self.env['kit.component'].search_count([('active', '=', True)])
            record.total_templates = self.env['kit.template'].search_count([('active', '=', True)])
    
    @api.depends_context('uid') 
    def _compute_financial(self):
        for record in self:
            sheets = self.env['kit.cost.sheet'].search([('state', 'in', ['calculated', 'confirmed'])])
            if sheets:
                total = sum(sheets.mapped('enabled_amount'))
                record.total_value = total
                record.average_value = total / len(sheets)
            else:
                record.total_value = 0.0
                record.average_value = 0.0
    
    def action_create_cost_sheet(self):
        return {
            'name': _('Create Cost Sheet'),
            'type': 'ir.actions.act_window',
            'res_model': 'kit.cost.calculator.wizard',
            'view_mode': 'form',
            'target': 'new',
        }