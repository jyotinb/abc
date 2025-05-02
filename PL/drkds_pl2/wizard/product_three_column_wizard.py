from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class ProductThreeColumnWizard(models.TransientModel):
    _name = 'drkds_pl2.product_three_column_wizard'
    _description = 'Product Three Column Report Wizard'
    
    customer_id = fields.Many2one('res.partner', string='Customer', domain=[('customer_rank', '>', 0)], required=True)
    contact_id = fields.Many2one('res.partner', string='Contact', domain="[('parent_id', '=', customer_id)]")
    salesman_id = fields.Many2one('res.users', string='Salesman', domain=[('share', '=', False)], required=False)
    price_level = fields.Selection([
        ('1', 'Price Level 1'),
        ('2', 'Price Level 2'),
        ('3', 'Price Level 3'),
        ('4', 'Price Level 4'),
        ('all', 'All Price Levels'),
    ], string='Price Level', default='all', required=True)
    doc_id = fields.Many2one('mrp.bom.cost.calculator', string='Cost Calculator Document', readonly=True)
    is_multi_product = fields.Boolean(related='doc_id.is_multi_product', readonly=True)
    
    # Products from the current document - define explicit relation tables
    available_product_ids = fields.Many2many(
        'product.product', 
        'drkds_pl2_wizard_available_products_rel',
        'wizard_id', 'product_id',
        string='Available Products', 
        readonly=True
    )
    
    selected_product_ids = fields.Many2many(
        'product.product',
        'drkds_pl2_wizard_selected_products_rel',
        'wizard_id', 'product_id',
        string='Selected Products'
    )
    
    product_order = fields.Selection([
        ('name', 'Name'),
        ('default_code', 'Internal Reference'),
        ('list_price', 'Price'),
        ('create_date', 'Creation Date'),
        ('custom', 'Custom Order'),
    ], string='Product Order', default='name', required=True)
    product_sequence_ids = fields.One2many('drkds_pl2.product_sequence', 'wizard_id', string='Custom Product Order')
    use_custom_sequence = fields.Boolean(compute='_compute_use_custom_sequence')
    
    @api.model
    def default_get(self, fields_list):
        """Load products from the active model/records"""
        res = super(ProductThreeColumnWizard, self).default_get(fields_list)
        
        # Get active model and ids from context
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        
        _logger.info("ProductThreeColumnWizard default_get - active_model: %s, active_id: %s", 
                     active_model, active_id)
        
        if active_model == 'mrp.bom.cost.calculator' and active_id:
            doc = self.env[active_model].browse(active_id)
            res['doc_id'] = doc.id
            
            # Get products from the document
            products = self.env['product.product']
            
            if doc.is_multi_product and doc.product_line_ids:
                # For multi-product documents, get products from product_line_ids
                _logger.info("Getting products from product_line_ids")
                products = doc.product_line_ids.mapped('product_id')
                _logger.info("Found %s products", len(products))
            elif doc.product_id:
                # For single product documents
                _logger.info("Getting single product: %s", doc.product_id.name)
                products = doc.product_id
            
            if products:
                _logger.info("Setting available and selected products: %s", 
                             products.mapped('name'))
                res['available_product_ids'] = [(6, 0, products.ids)]
                res['selected_product_ids'] = [(6, 0, products.ids)]  # Select all by default
            else:
                _logger.warning("No products found in document")
                
        return res
    
    @api.depends('product_order')
    def _compute_use_custom_sequence(self):
        for record in self:
            record.use_custom_sequence = record.product_order == 'custom'
    
    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        """Clear contact when customer changes"""
        self.contact_id = False
    
    @api.onchange('product_order')
    def _onchange_product_order(self):
        """When switching to custom order, create sequence records"""
        if self.product_order == 'custom' and self.selected_product_ids:
            # Clear existing sequence records first
            self.product_sequence_ids = [(5, 0, 0)]
            
            # Create new sequence records for each selected product
            sequence_vals = []
            for i, product in enumerate(self.selected_product_ids):
                sequence_vals.append((0, 0, {
                    'product_id': product.id,
                    'sequence': i + 1,
                    'product_name': product.display_name,  # Set the product name explicitly
                }))
            
            if sequence_vals:
                self.product_sequence_ids = sequence_vals
        # If switching away from custom order, clean up the sequence records
        elif self.product_order != 'custom':
            self.product_sequence_ids = [(5, 0, 0)]
    
    @api.onchange('selected_product_ids')
    def _onchange_selected_product_ids(self):
        """Update sequence records when products change"""
        if self.product_order == 'custom':
            # Get existing products in sequence
            existing_products = self.product_sequence_ids.mapped('product_id')
            # Add new products to sequence
            sequence_vals = []
            max_sequence = max(self.product_sequence_ids.mapped('sequence') or [0])
            for product in self.selected_product_ids:
                if product not in existing_products:
                    max_sequence += 1
                    sequence_vals.append((0, 0, {
                        'product_id': product.id,
                        'sequence': max_sequence,
                    }))
            # Remove products that are no longer selected
            for seq in self.product_sequence_ids:
                if seq.product_id not in self.selected_product_ids:
                    sequence_vals.append((2, seq.id, 0))
            
            self.product_sequence_ids = sequence_vals
    
    def action_print_report(self):
        """Launch the report with the selected parameters"""
        self.ensure_one()
        
        # Create a log record
        self.env['drkds_pl2.product_report_log'].create({
            'customer_id': self.customer_id.id,
            'contact_id': self.contact_id.id if self.contact_id else False,
            'salesman_id': self.salesman_id.id, 
            'price_level': self.price_level,
            'doc_id': self.doc_id.id,
        })
        
        # Get ordered products based on selected order method
        ordered_products = self.selected_product_ids
        if self.selected_product_ids:
            if self.product_order == 'custom' and self.product_sequence_ids:
                # Use custom sequence order
                sequence_records = self.product_sequence_ids.sorted(lambda r: r.sequence)
                ordered_products = sequence_records.mapped('product_id')
                _logger.info("Using custom order with %s products in order: %s", 
                             len(ordered_products), ordered_products.mapped('name'))
            else:
                # Use standard ordering
                order_field = self.product_order
                _logger.info("Sorting products by field: %s", order_field)
                ordered_products = self.env['product.product'].browse(self.selected_product_ids.ids).sorted(
                    lambda p: getattr(p, order_field, '')
                )
                _logger.info("Standard ordering resulted in %s products in order: %s", 
                             len(ordered_products), ordered_products.mapped('name'))
        
        # Prepare the data to send to the report
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'customer_id': self.customer_id.id,
                'customer_name': self.customer_id.name,
                'contact_id': self.contact_id.id if self.contact_id else False,
                'contact_name': self.contact_id.name if self.contact_id else '',
                'salesman_id': self.salesman_id.id,
                'salesman_name': self.salesman_id.name,
                'price_level': self.price_level,
                'doc_id': self.doc_id.id,
                'is_multi_product': self.is_multi_product,
                'product_ids': ordered_products.ids if ordered_products else [],
            }
        }
        
        _logger.info("Sending data to report with %s products", len(data['form']['product_ids']))
        
        # Return action to open the report
        return self.env.ref('drkds_pl2.action_report_product_three_column').report_action(self.doc_id, data=data)


# New model for custom product ordering
class ProductSequence(models.TransientModel):
    _name = 'drkds_pl2.product_sequence'
    _description = 'Custom Product Sequence'
    _order = 'sequence'
    
    wizard_id = fields.Many2one('drkds_pl2.product_three_column_wizard', string='Wizard', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    product_name = fields.Char(related='product_id.display_name', string='Product Name', readonly=True, store=True)