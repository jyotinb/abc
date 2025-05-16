# from odoo import api, fields, models, _
# import base64
# import xlsxwriter
# import io
# from datetime import datetime


# class PaymentExportWizard(models.TransientModel):
    # _name = 'payment.export.wizard'
    # _description = 'Export Payments to Excel'
    
    # date_from = fields.Date(string='Date From', required=True)
    # date_to = fields.Date(string='Date To', required=True)
    # partner_id = fields.Many2one('res.partner', string='Partner')
    # state = fields.Selection([
        # ('draft', 'Draft'),
        # ('confirmed', 'Confirmed'),
        # ('paid', 'Paid'),
        # ('all', 'All')
    # ], string='Status', default='all', required=True)
    
    # def action_export_excel(self):
        # # Create domain based on filters
        # domain = [('payment_sheet_id.date', '>=', self.date_from), 
                 # ('payment_sheet_id.date', '<=', self.date_to)]
        # if self.partner_id:
            # domain.append(('partner_id', '=', self.partner_id.id))
        # if self.state != 'all':
            # domain.append(('payment_sheet_id.state', '=', self.state))
        
        # # Get payment lines based on domain
        # payment_lines = self.env['payment.sheet.line'].search(domain)
        
        # if not payment_lines:
            # return {
                # 'type': 'ir.actions.client',
                # 'tag': 'display_notification',
                # 'params': {
                    # 'title': _('No Data'),
                    # 'message': _('No payments found matching the criteria.'),
                    # 'sticky': False,
                # }
            # }
        
        # # Create Excel file
        # output = io.BytesIO()
        # workbook = xlsxwriter.Workbook(output)
        # worksheet = workbook.add_worksheet('Payments')
        
        # # Define styles
        # header_style = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#EEEEEE', 'border': 1})
        # cell_style = workbook.add_format({'align': 'left', 'border': 1})
        # amount_style = workbook.add_format({'num_format': '#,##0.00', 'align': 'right', 'border': 1})
        # date_style = workbook.add_format({'num_format': 'dd/mm/yyyy', 'align': 'center', 'border': 1})
        
        # # Write header
        # headers = ['Sheet Reference', 'Sheet Date', 'Status', 'Partner', 'Account Name', 
                  # 'Account No', 'IFSC Code', 'Amount', 'Remarks']
        # for col, header in enumerate(headers):
            # worksheet.write(0, col, header, header_style)
        
        # # Write data
        # row = 1
        # for line in payment_lines:
            # worksheet.write(row, 0, line.payment_sheet_id.name, cell_style)
            # worksheet.write(row, 1, line.payment_sheet_id.date, date_style)
            # worksheet.write(row, 2, dict(line.payment_sheet_id._fields['state'].selection).get(line.payment_sheet_id.state), cell_style)
            # worksheet.write(row, 3, line.partner_id.name, cell_style)
            # worksheet.write(row, 4, line.account_name, cell_style)
            # worksheet.write(row, 5, line.account_no, cell_style)
            # worksheet.write(row, 6, line.ifsc_code, cell_style)
            # worksheet.write(row, 7, line.amount, amount_style)
            # worksheet.write(row, 8, line.remarks or '', cell_style)
            # row += 1
        
        # # Add a total row
        # worksheet.write(row, 3, 'Total', header_style)
        # worksheet.write(row, 7, f'=SUM(H2:H{row})', amount_style)
        
        # # Adjust column widths
        # worksheet.set_column(0, 0, 15)  # Sheet Reference
        # worksheet.set_column(1, 1, 12)  # Sheet Date
        # worksheet.set_column(2, 2, 10)  # Status
        # worksheet.set_column(3, 3, 25)  # Partner
        # worksheet.set_column(4, 4, 25)  # Account Name
        # worksheet.set_column(5, 5, 20)  # Account No
        # worksheet.set_column(6, 6, 15)  # IFSC Code
        # worksheet.set_column(7, 7, 12)  # Amount
        # worksheet.set_column(8, 8, 40)  # Remarks
        
        # workbook.close()
        # output.seek(0)
        
        # # Create attachment
        # filename = f"Bank_Payments_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
        # attachment_vals = {
            # 'name': filename,
            # 'datas': base64.b64encode(output.read()),
            # 'res_model': 'payment.export.wizard',
            # 'res_id': self.id,
            # 'type': 'binary',
        # }
        # attachment = self.env['ir.attachment'].create(attachment_vals)
        
        # # Return download action
        # return {
            # 'type': 'ir.actions.act_url',
            # 'url': f'/web/content/{attachment.id}?download=true',
            # 'target': 'self',
        # }


from odoo import api, fields, models, _
import base64
import xlwt
import io
from datetime import datetime


class PaymentExportWizard(models.TransientModel):
    _name = 'payment.export.wizard'
    _description = 'Export Payments to Excel'

    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('all', 'All')
    ], string='Status', default='all', required=True)

    def action_export_excel(self):
        domain = [
            ('payment_sheet_id.date', '>=', self.date_from),
            ('payment_sheet_id.date', '<=', self.date_to)
        ]
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.state != 'all':
            domain.append(('payment_sheet_id.state', '=', self.state))

        payment_lines = self.env['payment.sheet.line'].search(domain)

        if not payment_lines:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Data'),
                    'message': _('No payments found matching the criteria.'),
                    'sticky': False,
                }
            }

        # Create Excel using xlwt
        output = io.BytesIO()
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Payments')

        # Define styles
        header_style = xlwt.easyxf('font: bold on; align: horiz center; pattern: pattern solid, fore_color gray25; borders: all thin;')
        cell_style = xlwt.easyxf('borders: all thin; align: horiz left;')
        amount_style = xlwt.easyxf('borders: all thin; align: horiz right;', num_format_str='#,##0.00')
        date_style = xlwt.easyxf('borders: all thin; align: horiz center;', num_format_str='DD/MM/YYYY')

        # Write headers
        headers = ['Sheet Reference', 'Sheet Date', 'Status', 'Partner', 'Account Name',
                   'Account No', 'IFSC Code', 'Amount', 'Remarks']
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_style)
            sheet.col(col).width = 5000  # Set default column width

        # Write data rows
        row = 1
        total_amount = 0.0
        for line in payment_lines:
            sheet.write(row, 0, line.payment_sheet_id.name or '', cell_style)
            sheet.write(row, 1, line.payment_sheet_id.date, date_style)
            sheet.write(row, 2, dict(line.payment_sheet_id._fields['state'].selection).get(line.payment_sheet_id.state, ''), cell_style)
            sheet.write(row, 3, line.partner_id.name or '', cell_style)
            sheet.write(row, 4, line.account_name or '', cell_style)
            sheet.write(row, 5, line.account_no or '', cell_style)
            sheet.write(row, 6, line.ifsc_code or '', cell_style)
            sheet.write(row, 7, line.amount, amount_style)
            sheet.write(row, 8, line.remarks or '', cell_style)
            total_amount += line.amount
            row += 1

        # Write total row
        sheet.write(row, 3, 'Total', header_style)
        sheet.write(row, 7, total_amount, amount_style)

        # Save to BytesIO
        workbook.save(output)
        output.seek(0)

        # Create attachment
        filename = f"Bank_Payments_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xls"
        attachment_vals = {
            'name': filename,
            'datas': base64.b64encode(output.read()),
            'res_model': 'payment.export.wizard',
            'res_id': self.id,
            'type': 'binary',
        }
        attachment = self.env['ir.attachment'].create(attachment_vals)

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
