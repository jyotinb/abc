# from odoo import models, fields, api
# from datetime import datetime, timedelta
#
# class PurchaseDateWizard(models.TransientModel):
#     _name = 'purchase.date.wizard'
#     _description = 'Wizard to Filter Purchase Orders by Date'
#
#     selected_date = fields.Date(string="Select Date", required=True, default=fields.Date.context_today)
#
#     def action_show_filtered_orders(self):
#         """Open the Daily Report filtered by selected date"""
#         #  Use correct module name
#         action = self.env.ref('purchase_report.action_purchase_daily_report').read()[0]
#
#         # Correct date range logic (from 00:00 to 23:59)
#         start_date = datetime.combine(self.selected_date, datetime.min.time())
#         end_date = start_date + timedelta(days=1)
#
#         #  Filter purchase orders created on selected date
#         action['domain'] = [
#             ('date_order', '>=', start_date),
#             ('date_order', '<', end_date)
#         ]
#         return action

from odoo import models, fields
from datetime import datetime, timedelta

class PurchaseDateWizard(models.TransientModel):
    _name = 'purchase.date.wizard'
    _description = 'Wizard to Filter Purchase Orders by Date'

    selected_date = fields.Date(string="Select Date", required=True, default=fields.Date.context_today)

    def action_show_filtered_orders(self):
        action = self.env.ref('purchase_report.action_purchase_daily_report').read()[0]

        start_date = datetime.combine(self.selected_date, datetime.min.time())
        end_date = start_date + timedelta(days=1)

        action['domain'] = [
            ('date_order', '>=', start_date.strftime('%Y-%m-%d %H:%M:%S')),
            ('date_order', '<', end_date.strftime('%Y-%m-%d %H:%M:%S')),
        ]
        action['target'] = 'current'
        return action
