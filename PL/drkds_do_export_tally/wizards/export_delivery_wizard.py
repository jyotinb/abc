import base64
import io
from odoo import models, fields, api
import xlsxwriter
from collections import defaultdict

class ExportDeliveryWizard(models.TransientModel):
    _name = 'export.delivery.wizard'
    _description = 'Export Delivery Order to Tally Wizard'
    
    picking_id = fields.Many2one(
        'stock.picking', 
        string='Delivery Order',
        required=True
    )
    include_price = fields.Boolean(
        string='Include Price',
        default=True,
        help="Include product price in the export"
    )
    excel_file = fields.Binary(
        string='Excel File',
        readonly=True
    )
    file_name = fields.Char(
        string='File Name',
        readonly=True
    )
    
    def action_export_to_excel(self):
        """Export delivery order details to Excel in Tally format"""
        self.ensure_one()
        
        # Create an in-memory output file
        output = io.BytesIO()
        
        # Create a workbook and add a worksheet
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Tally Export')
        
        # Define header row
        header = [
            'Date', 'Voucher Type', 'Invoice Number', 'Ledger Name', 
            'Ledger Amt', 'DrCr', 'Item Name', 'Quantity', 'UOM', 
            'Rate', 'Value', 'Change Mode', 'Location', 'Buyer',
            'Consignee', 'SoNo', 'Terms', 'Buyer Address', 
            'Consignee Address', 'Buyer State', 'Consignee State', 
            'Buyer GSTN', 'Consignee GSTN', 'Consignee State', 
            'Buyer Pin', 'Consignee Pin', 'Place of Supply'
        ]
        
        # Write headers to the first row
        for col, header_text in enumerate(header):
            worksheet.write(0, col, header_text)
        
        picking = self.picking_id
        total_value = 0
        
        # Create a summary of items by product ID
        summary_items = defaultdict(lambda: {'qty': 0, 'price': 0, 'name': '', 'uom': ''})
        
        # Collect and aggregate data from delivery order
        for move_line in picking.move_line_ids:
            product = move_line.product_id
            
            # Skip if no product
            if not product:
                continue
                
            # Get product data
            done_qty = move_line.quantity
            product_name = product.name or ''
            
            # Try to get price from sale order line if available
            price = 0.0
            if picking.sale_id:
                for line in picking.sale_id.order_line:
                    if line.product_id.id == product.id:
                        price = line.price_unit
                        break
            else:
                price = product.list_price
            
            # Add to summary
            summary_entry = summary_items[product.id]
            summary_entry['qty'] += done_qty
            summary_entry['name'] = product_name
            summary_entry['price'] = price  # Using the last found price
            if hasattr(move_line, 'product_uom_id') and move_line.product_uom_id:
                summary_entry['uom'] = move_line.product_uom_id.name
            elif hasattr(product, 'uom_id') and product.uom_id:
                summary_entry['uom'] = product.uom_id.name
        
        # Prepare item rows from summary
        item_rows = []
        for product_id, item_data in summary_items.items():
            value = item_data['qty'] * item_data['price']
            total_value += value
            
            # Prepare item row
            item_row = [
                picking.date_done.strftime('%d-%m-%Y') if picking.date_done else '',  # Date
                'Sales Order',  # Voucher Type
                picking.name,  # Invoice Number
                'Sales A/c',  # Ledger Name
                value,  # Ledger Amt
                'Cr',  # DrCr - Credit for items
                item_data['name'],  # Item Name
                item_data['qty'],  # Quantity
                item_data['uom'],  # UOM
                item_data['price'],  # Rate
                value,  # Value
                'Item Invoice',  # Change Mode
                '1',  # Location
                # Empty fields can be filled as needed
                '',  # Buyer
                '',  # Consignee
                picking.sale_id.name if picking.sale_id else '',  # SoNo
            ]
            
            item_rows.append(item_row)
        
        # First line - Customer row (Dr entry)
        first_row = [
            picking.date_done.strftime('%d-%m-%Y') if picking.date_done else '',  # Date
            'Sales Order',  # Voucher Type
            picking.name,  # Invoice Number
            picking.partner_id.name if picking.partner_id else '',  # Ledger Name - Receivables
            total_value + 0.04,  # Ledger Amt - Total value + 0.04 (0.01 * 4 for taxes)
            'Dr',  # DrCr - Debit for customer
            '',  # Item Name
            '',  # Quantity
            '',  # UOM
            '',  # Rate
            '',  # Value
            'Item Invoice',  # Change Mode
            '',  # Location
            '',  # Buyer
            '',  # Consignee
            picking.sale_id.name if picking.sale_id else '',  # SoNo
        ]
        
        # Write first row (row 1, after headers)
        for col, value in enumerate(first_row):
            worksheet.write(1, col, value)
        
        # Write item rows starting from row 2
        for row_idx, row_data in enumerate(item_rows, start=2):
            for col, value in enumerate(row_data):
                worksheet.write(row_idx, col, value)
        
        # Current row index after writing item rows
        current_row = 2 + len(item_rows)
        
        # Add tax rows with 0.01 value
        tax_entries = [
            "Packing & Forwarding (Local)",
            "SGST SALES A/C",
            "CGST SALES A/C",
            "IGST SALES A/C"
            
        ]
        
        for tax in tax_entries:
            # Create a row with empty values
            row_data = [''] * len(header)
            
            # Fill in the tax row data
            row_data[0] = picking.date_done.strftime('%d-%m-%Y') if picking.date_done else ''
            row_data[1] = 'Sales Order'
            row_data[2] = picking.name
            row_data[3] = tax
            row_data[4] = 0.01  # Setting Ledger Amt to 0.01
            row_data[5] = 'Cr'
            row_data[15] = picking.sale_id.name if picking.sale_id else ''
            
            # Write row to worksheet
            for col, value in enumerate(row_data):
                worksheet.write(current_row, col, value)
            
            current_row += 1
        
        # Close the workbook
        workbook.close()
        
        # Get the Excel data and encode it to base64
        excel_data = output.getvalue()
        encoded_excel = base64.b64encode(excel_data)
        
        # Close the BytesIO object
        output.close()
        
        # Update wizard with file data
        self.write({
            'excel_file': encoded_excel,
            'file_name': f'{self.picking_id.name}_tally_export.xlsx',
        })
        
        # Return URL action to download the file
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model=export.delivery.wizard&id={self.id}&field=excel_file&filename={self.file_name}&download=true',
            'target': 'self',
        }