# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
import xlsxwriter
import io
import base64

_logger = logging.getLogger(__name__)

class ClampCalculationDetail(models.TransientModel):
    _name = 'clamp.calculation.detail'
    _description = 'Clamp Calculation Detail Wizard'
    
    green_master_id = fields.Many2one('green.master', string='Project', required=True)
    calculation_date = fields.Datetime('Calculation Date', default=fields.Datetime.now)
    
    green_master_display = fields.Char(
        string='Project', 
        compute='_compute_green_master_display',
        store=False
    )
    
    calculation_line_ids = fields.One2many(
        'clamp.calculation.detail.line', 
        'wizard_id', 
        string='Calculation Details'
    )
    
    total_quantity = fields.Integer('Total Clamp Quantity', compute='_compute_totals')
    total_cost = fields.Float('Total Clamp Cost', compute='_compute_totals')
    
    summary_by_size = fields.Html(
        string='Summary by Size',
        compute='_compute_summaries',
        store=False
    )
    
    summary_by_type = fields.Html(
        string='Summary by Type', 
        compute='_compute_summaries',
        store=False
    )
    
    @api.depends('green_master_id', 'green_master_id.customer')
    def _compute_green_master_display(self):
        for record in self:
            if record.green_master_id and record.green_master_id.customer:
                record.green_master_display = record.green_master_id.customer
            else:
                record.green_master_display = 'No Customer Selected'
    
    @api.depends('calculation_line_ids.quantity', 'calculation_line_ids.total_cost')
    def _compute_totals(self):
        for record in self:
            record.total_quantity = sum(record.calculation_line_ids.mapped('quantity'))
            record.total_cost = sum(record.calculation_line_ids.mapped('total_cost'))
    
    @api.depends('calculation_line_ids')
    def _compute_summaries(self):
        for record in self:
            record.summary_by_size = record._generate_size_summary()
            record.summary_by_type = record._generate_type_summary()
    
    def calculate_clamps(self):
        """Calculate clamp details from green.master"""
        self.calculation_line_ids.unlink()
        
        project = self.green_master_id
        clamp_details = project.get_clamp_calculation_details()
        
        for detail in clamp_details:
            self.env['clamp.calculation.detail.line'].create({
                'wizard_id': self.id,
                **detail
            })
        
        return True
    
    def _generate_size_summary(self):
        """Generate HTML summary grouped by size"""
        if not self.calculation_line_ids:
            return '<div class="alert alert-info">No data available. Please calculate clamps first.</div>'
        
        size_data = {}
        for line in self.calculation_line_ids:
            if line.clamp_type != 'Info' and line.quantity > 0:
                if line.size not in size_data:
                    size_data[line.size] = {
                        'full_clamp': 0,
                        'half_clamp': 0,
                        'l_joint': 0,
                        't_joint': 0,
                        'total': 0,
                        'cost': 0.0
                    }
                
                clamp_key = line.clamp_type.lower().replace(' ', '_')
                if clamp_key in size_data[line.size]:
                    size_data[line.size][clamp_key] += line.quantity
                
                size_data[line.size]['total'] += line.quantity
                size_data[line.size]['cost'] += line.total_cost
        
        # Generate HTML table
        html = '<table class="table table-sm table-bordered">'
        html += '<thead><tr>'
        html += '<th>Size</th><th>Full</th><th>Half</th><th>L Joint</th><th>T Joint</th><th>Total</th><th>Cost</th>'
        html += '</tr></thead><tbody>'
        
        for size, data in sorted(size_data.items()):
            html += f'<tr>'
            html += f'<td>{size}</td>'
            html += f'<td>{data["full_clamp"] if data["full_clamp"] > 0 else "-"}</td>'
            html += f'<td>{data["half_clamp"] if data["half_clamp"] > 0 else "-"}</td>'
            html += f'<td>{data["l_joint"] if data["l_joint"] > 0 else "-"}</td>'
            html += f'<td>{data["t_joint"] if data["t_joint"] > 0 else "-"}</td>'
            html += f'<td><strong>{data["total"]}</strong></td>'
            html += f'<td><strong>{data["cost"]:.2f}</strong></td>'
            html += f'</tr>'
        
        html += '</tbody></table>'
        return html
    
    def _generate_type_summary(self):
        """Generate HTML summary grouped by type"""
        # Similar implementation
        return '<div>Type summary will be shown here</div>'
    
    def action_export_excel(self):
        """Export clamp calculation to Excel"""
        if not self.calculation_line_ids:
            self.calculate_clamps()
        
        # Excel export implementation would go here
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Excel Export',
                'message': 'Excel export functionality will be implemented',
                'type': 'info',
            }
        }


class ClampCalculationDetailLine(models.TransientModel):
    _name = 'clamp.calculation.detail.line'
    _description = 'Clamp Calculation Detail Line'
    _order = 'sequence, category, component'
    
    wizard_id = fields.Many2one('clamp.calculation.detail', string='Wizard', required=True, ondelete='cascade')
    sequence = fields.Integer('Sequence', default=10)
    
    category = fields.Char('Category', required=True)
    component = fields.Char('Component', required=True)
    clamp_type = fields.Char('Clamp Type', required=True)
    size = fields.Char('Size', required=True)
    quantity = fields.Integer('Quantity', default=0)
    formula = fields.Text('Formula/Notes')
    unit_price = fields.Float('Unit Price', default=0.0)
    total_cost = fields.Float('Total Cost', compute='_compute_total_cost', store=True)
    
    @api.depends('quantity', 'unit_price')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.quantity * record.unit_price
