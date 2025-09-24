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
    
    # Main fields
    green_master_id = fields.Many2one('green.master', string='Project', required=True)
    calculation_date = fields.Datetime('Calculation Date', default=fields.Datetime.now)
    
    # Display field for project
    green_master_display = fields.Char(
        string='Project', 
        compute='_compute_green_master_display',
        store=False
    )

    @api.depends('green_master_id', 'green_master_id.customer')
    def _compute_green_master_display(self):
        for record in self:
            if record.green_master_id and record.green_master_id.customer:
                record.green_master_display = record.green_master_id.customer
            else:
                record.green_master_display = 'No Customer Selected'
    
    # Calculation lines
    calculation_line_ids = fields.One2many(
        'clamp.calculation.detail.line', 
        'wizard_id', 
        string='Calculation Details'
    )
    
    # Summary fields
    total_quantity = fields.Integer('Total Clamp Quantity', compute='_compute_totals')
    total_cost = fields.Float('Total Clamp Cost', compute='_compute_totals')
    
    # Summary HTML fields
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
    
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self._context.get('active_id') and self._context.get('active_model') == 'green.master':
            res['green_master_id'] = self._context.get('active_id')
        return res
    
    def calculate_clamps(self):
        """Main method to calculate all clamp details using green.master methods"""
        self.calculation_line_ids.unlink()
        
        project = self.green_master_id
        
        # Get the detailed clamp calculations from the main model
        clamp_details = project.get_clamp_calculation_details()
        
        # Create calculation lines from the details
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
        
        # Group by size
        size_data = {}
        for line in self.calculation_line_ids:
            if line.clamp_type != 'Info' and line.quantity > 0:  # Skip info lines
                if line.size not in size_data:
                    size_data[line.size] = {
                        'full_clamp': 0,
                        'half_clamp': 0,
                        'l_joint': 0,
                        't_joint': 0,
                        'total': 0,
                        'cost': 0.0
                    }
                
                # Map clamp types to dict keys
                clamp_key = line.clamp_type.lower().replace(' ', '_')
                if clamp_key in size_data[line.size]:
                    size_data[line.size][clamp_key] += line.quantity
                
                size_data[line.size]['total'] += line.quantity
                size_data[line.size]['cost'] += line.total_cost
        
        if not size_data:
            return '<div class="alert alert-warning">No clamp data found in calculations.</div>'
        
        # Generate HTML table
        html = """
        <table class="table table-sm table-bordered table-striped">
            <thead class="thead-dark">
                <tr>
                    <th style="background-color: #4472C4; color: white;">Size</th>
                    <th style="background-color: #4472C4; color: white; text-align: center;">Full Clamp</th>
                    <th style="background-color: #4472C4; color: white; text-align: center;">Half Clamp</th>
                    <th style="background-color: #4472C4; color: white; text-align: center;">L Joint</th>
                    <th style="background-color: #4472C4; color: white; text-align: center;">T Joint</th>
                    <th style="background-color: #4472C4; color: white; text-align: center;">Total Qty</th>
                    <th style="background-color: #4472C4; color: white; text-align: right;">Total Cost</th>
                </tr>
            </thead>
            <tbody>
        """
        
        # Sort sizes for better display
        sorted_sizes = sorted(size_data.keys(), key=lambda x: self._parse_size_for_sorting(x))
        
        for size in sorted_sizes:
            data = size_data[size]
            html += f"""
                <tr>
                    <td><strong>{size}</strong></td>
                    <td style="text-align: center;">{data['full_clamp'] if data['full_clamp'] > 0 else '-'}</td>
                    <td style="text-align: center;">{data['half_clamp'] if data['half_clamp'] > 0 else '-'}</td>
                    <td style="text-align: center;">{data['l_joint'] if data['l_joint'] > 0 else '-'}</td>
                    <td style="text-align: center;">{data['t_joint'] if data['t_joint'] > 0 else '-'}</td>
                    <td style="text-align: center;"><strong>{data['total']}</strong></td>
                    <td style="text-align: right;"><strong>{data['cost']:.2f}</strong></td>
                </tr>
            """
        
        # Add totals row
        total_full = sum(d['full_clamp'] for d in size_data.values())
        total_half = sum(d['half_clamp'] for d in size_data.values())
        total_l = sum(d['l_joint'] for d in size_data.values())
        total_t = sum(d['t_joint'] for d in size_data.values())
        grand_total = sum(d['total'] for d in size_data.values())
        total_cost = sum(d['cost'] for d in size_data.values())
        
        html += f"""
            </tbody>
            <tfoot>
                <tr style="background-color: #D9E2F3; font-weight: bold;">
                    <th>TOTAL</th>
                    <th style="text-align: center;">{total_full}</th>
                    <th style="text-align: center;">{total_half}</th>
                    <th style="text-align: center;">{total_l}</th>
                    <th style="text-align: center;">{total_t}</th>
                    <th style="text-align: center;">{grand_total}</th>
                    <th style="text-align: right;">{total_cost:.2f}</th>
                </tr>
            </tfoot>
        </table>
        
        <div class="mt-3">
            <h5>Summary Statistics</h5>
            <ul>
                <li>Total Unique Sizes: <strong>{len(size_data)}</strong></li>
                <li>Most Used Size: <strong>{max(size_data.items(), key=lambda x: x[1]['total'])[0] if size_data else 'N/A'}</strong></li>
                <li>Average Clamps per Size: <strong>{grand_total / len(size_data) if size_data else 0:.1f}</strong></li>
            </ul>
        </div>
        """
        
        return html
    
    def _generate_type_summary(self):
        """Generate HTML summary grouped by clamp type"""
        if not self.calculation_line_ids:
            return '<div class="alert alert-info">No data available. Please calculate clamps first.</div>'
        
        # Group by type
        type_data = {}
        category_breakdown = {}  # Track categories for each type
        
        for line in self.calculation_line_ids:
            if line.clamp_type != 'Info' and line.quantity > 0:  # Skip info lines
                if line.clamp_type not in type_data:
                    type_data[line.clamp_type] = {
                        'sizes': {},
                        'total_qty': 0,
                        'total_cost': 0.0
                    }
                    category_breakdown[line.clamp_type] = set()
                
                type_data[line.clamp_type]['total_qty'] += line.quantity
                type_data[line.clamp_type]['total_cost'] += line.total_cost
                category_breakdown[line.clamp_type].add(line.category)
                
                # Track sizes
                if line.size not in type_data[line.clamp_type]['sizes']:
                    type_data[line.clamp_type]['sizes'][line.size] = 0
                type_data[line.clamp_type]['sizes'][line.size] += line.quantity
        
        if not type_data:
            return '<div class="alert alert-warning">No clamp data found in calculations.</div>'
        
        # Generate HTML
        html = """
        <table class="table table-sm table-bordered table-striped">
            <thead class="thead-dark">
                <tr>
                    <th style="background-color: #4472C4; color: white;">Clamp Type</th>
                    <th style="background-color: #4472C4; color: white;">Size Distribution</th>
                    <th style="background-color: #4472C4; color: white; text-align: center;">Total Quantity</th>
                    <th style="background-color: #4472C4; color: white; text-align: right;">Total Cost</th>
                    <th style="background-color: #4472C4; color: white;">Used In Categories</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for clamp_type in sorted(type_data.keys()):
            data = type_data[clamp_type]
            
            # Format size distribution
            sorted_sizes = sorted(data['sizes'].keys(), key=lambda x: self._parse_size_for_sorting(x))
            size_parts = []
            for size in sorted_sizes:
                qty = data['sizes'][size]
                size_parts.append(f'<span class="badge badge-secondary">{size}: {qty}</span>')
            sizes_html = " ".join(size_parts)
            
            # Format categories
            categories = sorted(list(category_breakdown[clamp_type]))
            category_html = "<br>".join([f"<small>• {cat}</small>" for cat in categories])
            
            html += f"""
                <tr>
                    <td><strong>{clamp_type}</strong></td>
                    <td>{sizes_html}</td>
                    <td style="text-align: center;"><strong>{data['total_qty']}</strong></td>
                    <td style="text-align: right;"><strong>{data['total_cost']:.2f}</strong></td>
                    <td>{category_html}</td>
                </tr>
            """
        
        # Add totals row and percentage breakdown
        grand_total_qty = sum(d['total_qty'] for d in type_data.values())
        grand_total_cost = sum(d['total_cost'] for d in type_data.values())
        
        html += f"""
            </tbody>
            <tfoot>
                <tr style="background-color: #D9E2F3; font-weight: bold;">
                    <th colspan="2">GRAND TOTAL</th>
                    <th style="text-align: center;">{grand_total_qty}</th>
                    <th style="text-align: right;">{grand_total_cost:.2f}</th>
                    <th></th>
                </tr>
            </tfoot>
        </table>
        
        <div class="mt-3">
            <h5>Type Distribution Chart</h5>
            <div class="row">
        """
        
        # Add percentage breakdown
        for clamp_type in sorted(type_data.keys()):
            percentage = (type_data[clamp_type]['total_qty'] / grand_total_qty * 100) if grand_total_qty > 0 else 0
            html += f"""
                <div class="col-md-6 mb-2">
                    <div class="d-flex justify-content-between">
                        <span>{clamp_type}:</span>
                        <span><strong>{percentage:.1f}%</strong> ({type_data[clamp_type]['total_qty']} pcs)</span>
                    </div>
                    <div class="progress" style="height: 20px;">
                        <div class="progress-bar bg-info" role="progressbar" 
                             style="width: {percentage}%;" 
                             aria-valuenow="{percentage}" 
                             aria-valuemin="0" 
                             aria-valuemax="100">
                        </div>
                    </div>
                </div>
            """
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def _parse_size_for_sorting(self, size_str):
        """Parse size string for sorting (e.g., '25mm' -> 25)"""
        if size_str == 'N/A' or not size_str:
            return 9999
        
        import re
        # Handle different size formats (25mm, 25x25mm, etc.)
        match = re.search(r'(\d+)', size_str)
        if match:
            return int(match.group(1))
        return 0
    
    def action_export_excel(self):
        """Export clamp calculation details to Excel"""
        # First calculate if not done
        if not self.calculation_line_ids:
            self.calculate_clamps()
        
        # Create Excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Create main calculation sheet
        self._create_calculation_sheet(workbook)
        
        # Create summary sheets
        self._create_size_summary_sheet(workbook)
        self._create_type_summary_sheet(workbook)
        
        workbook.close()
        output.seek(0)
        
        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': f'Clamp_Calculations_{self.green_master_id.customer or "Project"}_{fields.Datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        
        output.close()
        
        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
    
    def _create_calculation_sheet(self, workbook):
        """Create the main calculation details sheet"""
        worksheet = workbook.add_worksheet('Clamp Calculations')
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        category_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9E2F3',
            'border': 1
        })
        
        data_format = workbook.add_format({
            'border': 1,
            'align': 'left'
        })
        
        number_format = workbook.add_format({
            'border': 1,
            'align': 'right'
        })
        
        currency_format = workbook.add_format({
            'border': 1,
            'align': 'right',
            'num_format': '#,##0.00'
        })
        
        # Set column widths
        worksheet.set_column('A:A', 25)  # Category
        worksheet.set_column('B:B', 30)  # Component
        worksheet.set_column('C:C', 15)  # Clamp Type
        worksheet.set_column('D:D', 12)  # Size
        worksheet.set_column('E:E', 10)  # Quantity
        worksheet.set_column('F:F', 40)  # Formula
        worksheet.set_column('G:G', 12)  # Unit Price
        worksheet.set_column('H:H', 15)  # Total Cost
        
        # Write headers
        headers = ['Category', 'Component', 'Clamp Type', 'Size', 'Quantity', 'Formula/Notes', 'Unit Price', 'Total Cost']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Write data
        row = 1
        current_category = None
        
        for line in self.calculation_line_ids:
            # Add category row if changed
            if line.category != current_category:
                worksheet.merge_range(row, 0, row, 7, line.category, category_format)
                current_category = line.category
                row += 1
            
            # Write line data
            worksheet.write(row, 0, '', data_format)
            worksheet.write(row, 1, line.component, data_format)
            worksheet.write(row, 2, line.clamp_type, data_format)
            worksheet.write(row, 3, line.size, data_format)
            worksheet.write(row, 4, line.quantity, number_format)
            worksheet.write(row, 5, line.formula or '', data_format)
            worksheet.write(row, 6, line.unit_price, currency_format)
            worksheet.write(row, 7, line.total_cost, currency_format)
            row += 1
        
        # Add totals row
        row += 1
        worksheet.merge_range(row, 0, row, 3, 'GRAND TOTAL', header_format)
        worksheet.write(row, 4, self.total_quantity, number_format)
        worksheet.write(row, 5, '', data_format)
        worksheet.write(row, 6, '', data_format)
        worksheet.write(row, 7, self.total_cost, currency_format)
        
        # Add project information
        row += 3
        worksheet.write(row, 0, 'Project:', header_format)
        worksheet.merge_range(row, 1, row, 3, self.green_master_id.customer or 'N/A', data_format)
        row += 1
        worksheet.write(row, 0, 'Calculation Date:', header_format)
        worksheet.merge_range(row, 1, row, 3, self.calculation_date.strftime('%Y-%m-%d %H:%M:%S'), data_format)
    
    def _create_size_summary_sheet(self, workbook):
        """Create size summary sheet in Excel"""
        worksheet = workbook.add_worksheet('Summary by Size')
        
        # Similar format definitions as main sheet
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        # Aggregate data by size
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
        
        # Write headers
        headers = ['Size', 'Full Clamp', 'Half Clamp', 'L Joint', 'T Joint', 'Total Qty', 'Total Cost']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Write data
        row = 1
        sorted_sizes = sorted(size_data.keys(), key=lambda x: self._parse_size_for_sorting(x))
        
        for size in sorted_sizes:
            data = size_data[size]
            worksheet.write(row, 0, size)
            worksheet.write(row, 1, data['full_clamp'])
            worksheet.write(row, 2, data['half_clamp'])
            worksheet.write(row, 3, data['l_joint'])
            worksheet.write(row, 4, data['t_joint'])
            worksheet.write(row, 5, data['total'])
            worksheet.write(row, 6, data['cost'])
            row += 1
    
    def _create_type_summary_sheet(self, workbook):
        """Create type summary sheet in Excel"""
        worksheet = workbook.add_worksheet('Summary by Type')
        
        # Similar aggregation and export logic for type summary
        # ... (implement similar to size summary)


class ClampCalculationDetailLine(models.TransientModel):
    _name = 'clamp.calculation.detail.line'
    _description = 'Clamp Calculation Detail Line'
    _order = 'sequence, category, component'
    
    wizard_id = fields.Many2one('clamp.calculation.detail', string='Wizard', required=True, ondelete='cascade')
    sequence = fields.Integer('Sequence', default=10)
    
    # Calculation details
    category = fields.Char('Category', required=True)
    component = fields.Char('Component', required=True)
    clamp_type = fields.Char('Clamp Type', required=True)
    size = fields.Char('Size', required=True)
    quantity = fields.Integer('Quantity', default=0)
    formula = fields.Text('Formula/Notes')
    
    # Pricing
    unit_price = fields.Float('Unit Price', default=0.0)
    total_cost = fields.Float('Total Cost', compute='_compute_total_cost', store=True)
    
    @api.depends('quantity', 'unit_price')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.quantity * record.unit_price