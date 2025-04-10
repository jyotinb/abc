from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockJvCalculationWizard(models.TransientModel):
    _name = 'stock.jv.calculation.wizard'
    _description = 'Stock JV Calculation Wizard'
    
    name = fields.Char('Reference', default=lambda self: _('New Calculation'))
    date = fields.Date('Date', default=fields.Date.context_today, required=True)
    line_ids = fields.One2many('stock.jv.calculation.wizard.line', 'wizard_id', string='Product Lines')
    company_id = fields.Many2one('res.company', string='Company', required=True, 
                                default=lambda self: self.env.company)
    
    @api.model
    def default_get(self, fields):
        res = super(StockJvCalculationWizard, self).default_get(fields)
        if 'line_ids' in fields and not res.get('line_ids'):
            # Add an empty line by default
            res['line_ids'] = [(0, 0, {})]
        return res
    
    def action_calculate(self):
        self.ensure_one()
        
        if not self.line_ids:
            raise UserError(_("Please add at least one product to calculate raw materials."))
        
        # Check if all lines have products and quantities
        for line in self.line_ids:
            if not line.product_id or line.product_qty <= 0:
                raise UserError(_("Please ensure all lines have a product and a positive quantity."))
        
        # Create calculation record
        calculation_vals = {
            'date': self.date,
            'company_id': self.company_id.id,
            'line_ids': [(0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.product_qty,
            }) for line in self.line_ids],
        }
        
        calculation = self.env['stock.jv.calculation'].create(calculation_vals)
        
        # Calculate raw materials
        result = calculation.calculate_raw_materials()
        
        return result
    
    @api.onchange('company_id')
    def onchange_company_id(self):
        """Clear lines when company changes to avoid BOM inconsistencies"""
        if self.company_id and self.line_ids:
            self.line_ids = [(5, 0, 0)]
            self.line_ids = [(0, 0, {})]


class StockJvCalculationWizardLine(models.TransientModel):
    _name = 'stock.jv.calculation.wizard.line'
    _description = 'Stock JV Calculation Wizard Line'
    
    wizard_id = fields.Many2one('stock.jv.calculation.wizard', string='Wizard Reference', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True, domain=[('type', 'in', ['product', 'consu'])])
    product_qty = fields.Float('Quantity', required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='UoM', related='product_id.uom_id', readonly=True)
    bom_id = fields.Many2one('mrp.bom', string='BOM', compute='_compute_bom_id')
    bom_available = fields.Boolean('BOM Available', compute='_compute_bom_id')
    
    @api.depends('product_id', 'wizard_id.company_id')
    def _compute_bom_id(self):
        for line in self:
            bom = False
            bom_available = False
            if line.product_id and line.wizard_id.company_id:
                # Direct search for the BOM instead of using _bom_find
                domain = [
                    '|',
                    ('product_id', '=', line.product_id.id),
                    '&',
                    ('product_id', '=', False),
                    ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
                    ('company_id', '=', line.wizard_id.company_id.id),
                ]
                bom = self.env['mrp.bom'].search(domain, limit=1)
                bom_available = bool(bom)
            line.bom_id = bom.id if bom else False
            line.bom_available = bom_available
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id.id
            
    def action_view_bom(self):
        self.ensure_one()
        if not self.bom_id:
            return
            
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.bom',
            'view_mode': 'form',
            'res_id': self.bom_id.id,
            'target': 'new',
        }