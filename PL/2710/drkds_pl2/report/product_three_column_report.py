from odoo import models, fields, api, _


class ProductThreeColumnReport(models.AbstractModel):
    _name = 'report.drkds_pl2.report_product_three_column'
    _description = 'Product Three Column Report Model'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            return {
                'doc_ids': docids,
                'doc_model': 'mrp.bom.cost.calculator',
                'docs': self.env['mrp.bom.cost.calculator'].browse(docids),
            }
        
        # Get the document
        doc = self.env['mrp.bom.cost.calculator'].browse(data['form']['doc_id'])
        
        # Get products in the correct order
        product_ids = data['form'].get('product_ids', [])
        ordered_products = self.env['product.product'].browse(product_ids)
        
        # Get salesman details if available
        salesman_email = False
        salesman_mobile = False
        if data['form'].get('salesman_id'):
            salesman = self.env['res.users'].browse(data['form']['salesman_id'])
            salesman_email = salesman.email
            salesman_mobile = salesman.mobile
        
        return {
            'doc_ids': [data['form']['doc_id']],
            'doc_model': 'mrp.bom.cost.calculator',
            'docs': doc,
            'data': data['form'],
            'products': ordered_products,
            'salesman_email': salesman_email,
            'salesman_mobile': salesman_mobile,
            'customer': self.env['res.partner'].browse(data['form']['customer_id']),
            'contact': self.env['res.partner'].browse(data['form']['contact_id']) if data['form']['contact_id'] else False,
        }