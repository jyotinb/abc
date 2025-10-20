from odoo import models, fields, api, exceptions

class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    mo_id = fields.Many2one('mrp.production', string='Manufacturing Order')

class AutoPackaging(models.Model):
    _inherit = 'mrp.production'

    package_start_no = fields.Integer(string='Package Starting Number', default=1)
    package_count = fields.Integer(string="Package Count", compute='_compute_package_count')
    qty_packaged = fields.Float(string="Quantity Packaged", default=0.0)
    is_packaged = fields.Boolean(string="Is Packaged", default=False)
    can_create_packages = fields.Boolean(string="Can Create Packages", compute="_compute_can_create_packages")

    def _compute_package_count(self):
        for production in self:
            production.package_count = self.env['stock.quant.package'].search_count([('mo_id', '=', production.id)])

    @api.depends('state', 'is_packaged')
    def _compute_can_create_packages(self):
        for production in self:
            production.can_create_packages = production.state == 'done' and not production.is_packaged

    def create_packages(self, package_type_id, package_qty):
        self.ensure_one()
        if not self.can_create_packages:
            raise exceptions.UserError('You can only create packages after the MO is done and not yet fully packaged.')

        produced_qty = min(package_qty, self.qty_producing - self.qty_packaged)
        product = self.product_id

        packaging = self.env['product.packaging'].browse(package_type_id)
        if not packaging:
            raise exceptions.UserError('No selected packaging type found.')

        num_packages = produced_qty // packaging.qty
        remainder_qty = produced_qty % packaging.qty

        for _ in range(int(num_packages)):
            sequence_number = self.env['ir.sequence'].next_by_code('stock.package')
            package_name = f'{packaging.name}-{sequence_number}'  # Combine the product packaging name with the sequence number
            package = self.env['stock.quant.package'].create({
                'name': package_name,
                'package_type_id': packaging.package_type_id.id,
                'mo_id': self.id,
            })
            self.env['stock.quant'].create({
                'product_id': product.id,
                'quantity': packaging.qty,
                'package_id': package.id,
                'location_id': self.location_dest_id.id,
            })

        if remainder_qty > 0:
            sequence_number = self.env['ir.sequence'].next_by_code('stock.package')
            package_name = f'{packaging.name}-{sequence_number}'  # Combine the product packaging name with the sequence number
            package = self.env['stock.quant.package'].create({
                'name': package_name,
                'package_type_id': packaging.package_type_id.id,
                'mo_id': self.id,
            })
            self.env['stock.quant'].create({
                'product_id': product.id,
                'quantity': remainder_qty,
                'package_id': package.id,
                'location_id': self.location_dest_id.id,
            })

        self.qty_packaged += produced_qty

        if self.qty_packaged >= self.product_qty:
            self.write({'is_packaged': True})

    def action_open_packaging_wizard(self):
        return {
            'name': 'Select Packaging Type',
            'type': 'ir.actions.act_window',
            'res_model': 'packaging.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_production_id': self.id,
                'default_product_id': self.product_id.id,
            },
        }

    def action_view_packages(self):
        self.ensure_one()
        return {
            'name': 'Packages',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'stock.quant.package',
            'domain': [('mo_id', '=', self.id)],
            'context': dict(self.env.context),
        }

    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'is_packaged': False,
            'qty_packaged': 0.0,
        })
        return super(AutoPackaging, self).copy(default)



from odoo import models, fields, api

class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    content_details = fields.Char(string="Package Contents", compute="_compute_content_details", store=True)

    @api.depends('quant_ids')
    def _compute_content_details(self):
        for record in self:
            details = []
            for quant in record.quant_ids:
                if quant.product_id and quant.product_uom_id:
                    details.append(f'[{quant.product_id.default_code}] - {quant.product_id.name} - {quant.quantity} {quant.product_uom_id.name} - --')
            record.content_details = "\n".join(details)
