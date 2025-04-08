from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class StockJvCalculation(models.Model):
    _name = 'stock.jv.calculation'
    _description = 'Stock JV Calculation'
    _order = 'date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    date = fields.Date('Date', default=fields.Date.context_today, required=True, tracking=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, required=True, tracking=True)
    line_ids = fields.One2many('stock.jv.calculation.line', 'calculation_id', string='Product Lines')
    result_ids = fields.One2many('stock.jv.calculation.result', 'calculation_id', string='Result Lines')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', readonly=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, 
                                 default=lambda self: self.env.company)
    context_today = fields.Boolean(compute='_compute_context_today')
    
    @api.depends_context('unit_mismatch_warning', 'subcontracting_warning')
    def _compute_context_today(self):
        for record in self:
            record.context_today = (
                self.env.context.get('unit_mismatch_warning', False) or 
                self.env.context.get('subcontracting_warning', False)
            )
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.jv.calculation') or _('New')
        return super(StockJvCalculation, self).create(vals_list)
    
    def calculate_raw_materials(self):
        self.ensure_one()
        
        if not self.line_ids:
            raise UserError(_("Please add at least one product to calculate raw materials."))
        
        # Clear previous results
        self.result_ids.unlink()
        
        # Dictionary to store raw material quantities
        raw_materials = {}
        
        # Track BOM unit mismatches
        unit_mismatches = []
        
        # Track subcontracting products
        subcontracted_products = []
        
        # Get list of top-level product IDs to exclude from raw materials
        top_level_ids = set(line.product_id.id for line in self.line_ids)
        
        # Process each product line
        for line in self.line_ids:
            product = line.product_id
            quantity = line.product_qty
            
            # Check if product has BOM
            boms = self.env['mrp.bom']._bom_find(product, company_id=self.company_id.id)
            bom = boms[product.id] if product.id in boms else False
            if bom and product.uom_id.id != bom.product_uom_id.id:
                unit_mismatches.append(_(
                    "Unit mismatch warning: Product '%s' uses '%s' but its BOM uses '%s'. Conversion will be applied."
                ) % (product.name, product.uom_id.name, bom.product_uom_id.name))
            
            # Check for subcontracting
            if bom and bom.type == 'subcontract':
                subcontracted_products.append(product.name)
                
            self._process_bom(product, quantity, raw_materials, 
                              is_top_level=True, 
                              track_subcontracting=True,
                              top_level_ids=top_level_ids)
        
        # Create result lines
        result_vals = []
        for raw_material_id, data in raw_materials.items():
            raw_material = self.env['product.product'].browse(raw_material_id)
            result_vals.append({
                'calculation_id': self.id,
                'product_id': raw_material_id,
                'product_qty': data['qty'],
                'product_uom': data['uom'],
                'has_uom_warning': False,
                'is_subcontracted': data.get('is_subcontracted', False),
                'is_supplied_to_subcontractor': data.get('is_supplied_to_subcontractor', False),
            })
        
        if result_vals:
            self.env['stock.jv.calculation.result'].create(result_vals)
        
        # Create notification for unit mismatches
        if unit_mismatches:
            message = _("The following unit mismatches were detected and automatically converted:\n")
            message += "\n".join(unit_mismatches)
            self.message_post(body=message)
            
        # Create notification for subcontracting
        if subcontracted_products:
            message = _("The following products involve subcontracting and their raw materials have been calculated:\n")
            message += "\n".join(subcontracted_products)
            self.message_post(body=message)
        
        self.write({'state': 'done'})
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Raw Material Calculation Result'),
            'res_model': 'stock.jv.calculation',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'unit_mismatch_warning': bool(unit_mismatches),
                'subcontracting_warning': bool(subcontracted_products),
            },
        }
    
    def _process_bom(self, product, quantity, raw_materials, is_top_level=True, track_subcontracting=False, subcontracted_path=False, top_level_ids=None):
        """
        Recursively process BOM to get all raw materials
        """
        # Initialize top_level_ids if not provided
        if top_level_ids is None and is_top_level:
            top_level_ids = set([product.id])
        elif top_level_ids is None:
            top_level_ids = set()
                
        # Find the BOM for this product using direct search - Odoo 17 compatible approach
        domain = [
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ('company_id', '=', self.company_id.id),
        ]
        
        # If we want to filter by BOM type, add it to the domain
        # domain.append(('type', '=', 'normal'))
        
        bom = self.env['mrp.bom'].search(domain, limit=1)
        
        # If no BOM found or can't use it
        if not bom:
            # If product is not in the top-level products list, add as raw material
            if product.id not in top_level_ids:
                if product.id not in raw_materials:
                    raw_materials[product.id] = {
                        'qty': 0.0,
                        'uom': product.uom_id.id,
                        'uom_category': product.uom_id.category_id.id,
                    }
                    
                    # Track if this is a subcontracting-related product
                    if track_subcontracting:
                        raw_materials[product.id]['is_subcontracted'] = False
                        raw_materials[product.id]['is_supplied_to_subcontractor'] = subcontracted_path
                        
                raw_materials[product.id]['qty'] += quantity
            return
        
   
    
    
        
        # Check if this is a subcontracting BOM
        is_subcontracting = bom.type == 'subcontract'
        
        # Check if product UoM and BOM UoM are different
        if is_top_level and product.uom_id.id != bom.product_uom_id.id:
            # Convert quantity to BOM UoM
            quantity = product.uom_id._compute_quantity(quantity, bom.product_uom_id)
            
        # Process each BOM line
        factor = quantity / bom.product_qty
        for line in bom.bom_line_ids:
            component = line.product_id
            
            # Calculate component quantity with proper unit conversion
            if line.product_uom_id.id != component.uom_id.id:
                line_qty = line.product_uom_id._compute_quantity(line.product_qty, component.uom_id) * factor
            else:
                line_qty = line.product_qty * factor
                
            # Check if component has BOM
            component_boms = self.env['mrp.bom']._bom_find(component, company_id=self.company_id.id)
            component_bom = component_boms[component.id] if component.id in component_boms else False
            
            # For subcontracting, we need to handle the supplied components
            in_subcontract_path = subcontracted_path or is_subcontracting
            
            # Track components specifically supplied to subcontractors
            if is_subcontracting and hasattr(line, 'is_supplied_by_customer') and line.is_supplied_by_customer:
                supplied_to_subcontractor = True
            else:
                supplied_to_subcontractor = subcontracted_path
                
            if component_bom:
                # If component has BOM, process recursively
                self._process_bom(
                    component, 
                    line_qty, 
                    raw_materials, 
                    is_top_level=False,
                    track_subcontracting=track_subcontracting,
                    subcontracted_path=supplied_to_subcontractor,
                    top_level_ids=top_level_ids
                )
            else:
                # If no BOM, add to raw materials
                if component.id not in raw_materials:
                    raw_materials[component.id] = {
                        'qty': 0.0,
                        'uom': component.uom_id.id,
                        'uom_category': component.uom_id.category_id.id,
                    }
                    
                    # Track if this is a subcontracting-related product
                    if track_subcontracting:
                        raw_materials[component.id]['is_subcontracted'] = is_subcontracting
                        raw_materials[component.id]['is_supplied_to_subcontractor'] = supplied_to_subcontractor
                        
                raw_materials[component.id]['qty'] += line_qty
                
        # For subcontracted BOMs, we need to add the finished product as a "raw material"
        # since we'll receive it from the vendor, but only if it's not in the top-level products list
        is_subcontracting = bom.type == 'subcontract'
        if is_subcontracting and track_subcontracting and product.id not in top_level_ids:
            if product.id not in raw_materials:
                raw_materials[product.id] = {
                    'qty': 0.0,
                    'uom': product.uom_id.id,
                    'uom_category': product.uom_id.category_id.id,
                    'is_subcontracted': True,
                    'is_supplied_to_subcontractor': False,
                }
            raw_materials[product.id]['qty'] += quantity
    
    def action_cancel(self):
        self.write({'state': 'cancel'})
    
    def action_draft(self):
        self.write({'state': 'draft'})
    
    def unlink(self):
        for record in self:
            if record.state == 'done':
                raise UserError(_("You cannot delete a calculation that is in 'Done' state."))
        return super(StockJvCalculation, self).unlink()


class StockJvCalculationLine(models.Model):
    _name = 'stock.jv.calculation.line'
    _description = 'Stock JV Calculation Line'
    
    calculation_id = fields.Many2one('stock.jv.calculation', string='Calculation Reference', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True, domain=[('type', 'in', ['product', 'consu'])])
    product_qty = fields.Float('Quantity', required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='UoM', related='product_id.uom_id', readonly=True)
    bom_id = fields.Many2one('mrp.bom', string='BOM', compute='_compute_bom_id', store=True)
    
    @api.depends('product_id')
    def _compute_bom_id(self):
        for line in self:
            bom = False
            if line.product_id and line.calculation_id and line.calculation_id.company_id:
                boms = self.env['mrp.bom']._bom_find(line.product_id, company_id=line.calculation_id.company_id.id)
                if line.product_id.id in boms:
                    bom = boms[line.product_id.id]
            line.bom_id = bom.id if bom else False
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id.id


class StockJvCalculationResult(models.Model):
    _name = 'stock.jv.calculation.result'
    _description = 'Stock JV Calculation Result'
    
    calculation_id = fields.Many2one('stock.jv.calculation', string='Calculation Reference', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Raw Material', required=True)
    product_qty = fields.Float('Required Quantity', required=True)
    product_uom = fields.Many2one('uom.uom', string='UoM', required=True)
    has_uom_warning = fields.Boolean('UoM Warning', default=False, 
                                     help="Indicates there was a unit of measure conversion in the BOM calculation")
    is_subcontracted = fields.Boolean('Is Subcontracted', default=False,
                                     help="This product is received from a subcontractor")
    is_supplied_to_subcontractor = fields.Boolean('Supplied to Subcontractor', default=False, 
                                               help="This material needs to be supplied to a subcontractor")