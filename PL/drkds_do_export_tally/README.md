# Delivery Order Export to Tally Module

This module adds functionality to export delivery order data to CSV in a format compatible with Tally accounting software.

## Features
- Export button on completed delivery orders
- Export includes sales order number, customer name, product, quantity, and price
- Format compatible with Tally import
- Includes ledger entries for GST accounting

## Installation
1. Copy this module to your Odoo addons directory
2. Update the module list in Odoo
3. Install the module through the Odoo interface

## Usage
1. Navigate to a completed delivery order
2. Click the "Export to Tally" button
3. Configure export options
4. Click "Export to Tally Format" to generate and download the CSV file
5. Import the downloaded file into Tally

## Tally Import Format
The exported CSV follows Tally's voucher import format:
- First row contains the customer entry (Dr)
- Item rows follow (Cr)
- Tax account rows are included at the end (Cr)

## Note
You may need to adjust tax amounts manually in Tally after import.
