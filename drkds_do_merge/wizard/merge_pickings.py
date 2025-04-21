from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class MergePickings(models.TransientModel):
    _name = 'stock.picking.merge.wizard'
    _description = 'Merge Delivery Orders'

    picking_ids = fields.Many2many(
        'stock.picking', string='Delivery Orders',
        domain="[('state', 'not in', ('done', 'cancel')), ('picking_type_id.code', '=', 'outgoing')]")
    
    dest_picking_id = fields.Many2one(
        'stock.picking', string='Destination Delivery Order',
        domain="[('id', 'in', picking_ids)]",
        help='Select which delivery order to keep. If not selected, a new one will be created.')
    
    merge_method = fields.Selection([
        ('new', 'Create a new delivery order'),
        ('existing', 'Merge into an existing delivery order')
    ], string='Merge Method', default='new', required=True)
    
    has_term_warnings = fields.Boolean(string='Has Term Warnings', compute='_compute_has_term_warnings')
    payment_term_warning = fields.Text(string='Payment Term Warnings', compute='_compute_term_warnings')
    delivery_term_warning = fields.Text(string='Delivery Term Warnings', compute='_compute_term_warnings')
    
    # Fields for final terms selection
    final_payment_term_id = fields.Many2one('account.payment.term', string='Final Payment Term')
    final_incoterm_id = fields.Many2one('account.incoterms', string='Final Delivery Term')
    has_payment_term_mismatch = fields.Boolean(string='Has Payment Term Mismatch', compute='_compute_term_mismatches')
    has_incoterm_mismatch = fields.Boolean(string='Has Incoterm Mismatch', compute='_compute_term_mismatches')
    available_payment_terms = fields.Many2many('account.payment.term', string='Available Payment Terms', 
                                            compute='_compute_available_terms')
    available_incoterms = fields.Many2many('account.incoterms', string='Available Incoterms',
                                          compute='_compute_available_terms')
    
    @api.onchange('merge_method')
    def _onchange_merge_method(self):
        if self.merge_method == 'new':
            self.dest_picking_id = False
    
    @api.onchange('picking_ids')
    def _onchange_picking_ids(self):
        if self.picking_ids:
            # Validate pickings are compatible (same partner, location, etc.)
            self._validate_compatible_pickings()
            
            # Set a default destination picking if merge method is 'existing'
            if self.merge_method == 'existing' and not self.dest_picking_id and self.picking_ids:
                self.dest_picking_id = self.picking_ids[0].id

    @api.depends('picking_ids')
    def _compute_has_term_warnings(self):
        for wizard in self:
            wizard.has_term_warnings = False
            if len(wizard.picking_ids) >= 2:
                wizard._validate_compatible_pickings()
                wizard.has_term_warnings = hasattr(wizard, 'term_warnings') and bool(wizard.term_warnings)
    
    @api.depends('has_term_warnings')
    def _compute_term_warnings(self):
        for wizard in self:
            wizard.payment_term_warning = ''
            wizard.delivery_term_warning = ''
            
            if hasattr(wizard, 'term_warnings') and wizard.term_warnings:
                payment_warnings = []
                delivery_warnings = []
                
                for warning in wizard.term_warnings:
                    if 'payment terms' in warning:
                        payment_warnings.append(warning)
                    elif 'delivery terms' in warning:
                        delivery_warnings.append(warning)
                
                wizard.payment_term_warning = '\n'.join(payment_warnings)
                wizard.delivery_term_warning = '\n'.join(delivery_warnings)
    
    @api.depends('picking_ids')
    def _compute_term_mismatches(self):
        for wizard in self:
            # Initialize
            wizard.has_payment_term_mismatch = False
            wizard.has_incoterm_mismatch = False
            
            if len(wizard.picking_ids) < 2:
                continue
                
            # Get unique sales orders
            sale_orders = self.env['sale.order']
            for picking in wizard.picking_ids:
                if hasattr(picking, 'sale_id') and picking.sale_id:
                    sale_orders |= picking.sale_id
                else:
                    # Check for sales orders through stock moves
                    for move in picking.move_ids:
                        if move.sale_line_id and move.sale_line_id.order_id:
                            sale_orders |= move.sale_line_id.order_id
            
            # Check payment terms
            payment_terms = sale_orders.mapped('payment_term_id')
            wizard.has_payment_term_mismatch = len(payment_terms) > 1
            
            # Check incoterms
            incoterms = sale_orders.mapped('incoterm')
            wizard.has_incoterm_mismatch = len(incoterms) > 1
            
            # Set default values for final terms if mismatches exist
            if wizard.has_payment_term_mismatch and not wizard.final_payment_term_id:
                # Prefer term from destination picking if using existing method
                if wizard.merge_method == 'existing' and wizard.dest_picking_id and wizard.dest_picking_id.sale_id:
                    wizard.final_payment_term_id = wizard.dest_picking_id.sale_id.payment_term_id
                # Otherwise use the most common term
                elif payment_terms:
                    term_counts = {}
                    for order in sale_orders:
                        term = order.payment_term_id
                        if term:
                            term_counts[term.id] = term_counts.get(term.id, 0) + 1
                    if term_counts:
                        most_common_term_id = max(term_counts, key=term_counts.get)
                        wizard.final_payment_term_id = self.env['account.payment.term'].browse(most_common_term_id)
            
            if wizard.has_incoterm_mismatch and not wizard.final_incoterm_id:
                # Prefer incoterm from destination picking if using existing method
                if wizard.merge_method == 'existing' and wizard.dest_picking_id and wizard.dest_picking_id.sale_id:
                    wizard.final_incoterm_id = wizard.dest_picking_id.sale_id.incoterm
                # Otherwise use the most common incoterm
                elif incoterms:
                    incoterm_counts = {}
                    for order in sale_orders:
                        incoterm = order.incoterm
                        if incoterm:
                            incoterm_counts[incoterm.id] = incoterm_counts.get(incoterm.id, 0) + 1
                    if incoterm_counts:
                        most_common_incoterm_id = max(incoterm_counts, key=incoterm_counts.get)
                        wizard.final_incoterm_id = self.env['account.incoterms'].browse(most_common_incoterm_id)
                        
    @api.depends('picking_ids')
    def _compute_available_terms(self):
        for wizard in self:
            payment_terms = self.env['account.payment.term']
            incoterms = self.env['account.incoterms']
            
            # Get unique sales orders
            sale_orders = self.env['sale.order']
            for picking in wizard.picking_ids:
                if hasattr(picking, 'sale_id') and picking.sale_id:
                    sale_orders |= picking.sale_id
                else:
                    # Check for sales orders through stock moves
                    for move in picking.move_ids:
                        if move.sale_line_id and move.sale_line_id.order_id:
                            sale_orders |= move.sale_line_id.order_id
            
            # Get unique terms
            payment_terms = sale_orders.mapped('payment_term_id')
            incoterms = sale_orders.mapped('incoterm')
            
            wizard.available_payment_terms = payment_terms
            wizard.available_incoterms = incoterms

    def _validate_compatible_pickings(self):
        
        if len(self.picking_ids) < 2:
            return
            
        reference_picking = self.picking_ids[0]
        for picking in self.picking_ids:
            if picking.picking_type_id != reference_picking.picking_type_id:
                raise ValidationError(_("Cannot merge delivery orders with different operation types."))
            if picking.partner_id != reference_picking.partner_id:
                raise ValidationError(_("Cannot merge delivery orders for different partners."))
            if picking.location_id != reference_picking.location_id:
                raise ValidationError(_("Cannot merge delivery orders with different source locations."))
            if picking.location_dest_id != reference_picking.location_dest_id:
                raise ValidationError(_("Cannot merge delivery orders with different destination locations."))
            if picking.state == 'done':
                raise ValidationError(_("Cannot merge already validated delivery orders."))
            if picking.state == 'cancel':
                raise ValidationError(_("Cannot merge cancelled delivery orders."))
            
            # Check for sales order terms mismatches and store warnings
            if hasattr(picking, 'sale_id') and picking.sale_id and hasattr(reference_picking, 'sale_id') and reference_picking.sale_id:
                # Check payment terms
                if picking.sale_id.payment_term_id != reference_picking.sale_id.payment_term_id:
                    if not hasattr(self, 'term_warnings'):
                        self.term_warnings = []
                    self.term_warnings.append(_(
                        "Warning: Orders have different payment terms. "
                        "Order %s has '%s' while order %s has '%s'") % (
                        picking.sale_id.name, picking.sale_id.payment_term_id.name or 'None',
                        reference_picking.sale_id.name, reference_picking.sale_id.payment_term_id.name or 'None'))
                
                # Check incoterms (delivery terms)
                if picking.sale_id.incoterm != reference_picking.sale_id.incoterm:
                    if not hasattr(self, 'term_warnings'):
                        self.term_warnings = []
                    self.term_warnings.append(_(
                        "Warning: Orders have different delivery terms (incoterms). "
                        "Order %s has '%s' while order %s has '%s'") % (
                        picking.sale_id.name, picking.sale_id.incoterm.name or 'None',
                        reference_picking.sale_id.name, reference_picking.sale_id.incoterm.name or 'None'))

    def action_merge_pickings(self):
        
        self._validate_compatible_pickings()
        
        if len(self.picking_ids) < 2:
            raise ValidationError(_("Select at least two delivery orders to merge."))
            
        # Validate final terms are selected if mismatches exist
        if self.has_payment_term_mismatch and not self.final_payment_term_id:
            raise ValidationError(_("Please select the final payment term to use for the merged delivery."))
        if self.has_incoterm_mismatch and not self.final_incoterm_id:
            raise ValidationError(_("Please select the final delivery term (incoterm) to use for the merged delivery."))
        
        # Determine destination picking
        if self.merge_method == 'existing':
            if not self.dest_picking_id:
                raise ValidationError(_("Please select a destination delivery order."))
            dest_picking = self.dest_picking_id
            source_pickings = self.picking_ids - dest_picking
        else:  # Create new picking
            # Get reference picking for defaults
            reference_picking = self.picking_ids[0]
            
            # Create new picking
            dest_picking = self.env['stock.picking'].create({
                'partner_id': reference_picking.partner_id.id,
                'picking_type_id': reference_picking.picking_type_id.id,
                'location_id': reference_picking.location_id.id,
                'location_dest_id': reference_picking.location_dest_id.id,
                'origin': _('Merge: %s') % ', '.join(self.picking_ids.mapped('name')),
                'scheduled_date': min(self.picking_ids.mapped('scheduled_date')),
                'company_id': reference_picking.company_id.id,
            })
            source_pickings = self.picking_ids
        
        # Copy all moves from source pickings to destination picking
        for source_picking in source_pickings:
            # Skip if it's the destination picking
            if source_picking == dest_picking:
                continue
                
            # Process each move
            for move in source_picking.move_ids:
                # Skip cancelled moves
                if move.state == 'cancel':
                    continue
                
                # Important: PRESERVE the sale_line_id to maintain price information
                new_move = move.copy({
                    'picking_id': dest_picking.id,
                    'state': 'draft',
                    'sale_line_id': move.sale_line_id.id,  # Preserve sales order line reference
                    'group_id': move.group_id.id,  # Preserve procurement group (links to sale order)
                    'origin_returned_move_id': False,
                    'price_unit': move.price_unit,  # Preserve original price
                })
                
                # Copy move lines if any
                if move.move_line_ids:
                    for move_line in move.move_line_ids:
                        move_line.copy({
                            'move_id': new_move.id,
                            'picking_id': dest_picking.id,
                            'state': 'draft',
                        })
            
            # Mark the original picking as merged
            source_picking.write({
                'merged_to_picking': [(4, dest_picking.id)],
            })
            
            # Cancel the source picking
            source_picking.action_cancel()
        
        # Prepare term information for the destination picking
        term_info = {
            'merged_from_pickings': [(4, p.id) for p in source_pickings if p != dest_picking]
        }
        
        # Add selected final terms
        if self.has_payment_term_mismatch:
            term_info['selected_payment_term_id'] = self.final_payment_term_id.id
        
        if self.has_incoterm_mismatch:
            term_info['selected_incoterm_id'] = self.final_incoterm_id.id
        
        # Add term mismatch notes
        term_notes = []
        if hasattr(self, 'term_warnings') and self.term_warnings:
            term_notes.extend(self.term_warnings)
        
        # Add notes about selected terms
        if self.has_payment_term_mismatch:
            term_notes.append(_("Selected final payment term: %s") % self.final_payment_term_id.name)
        
        if self.has_incoterm_mismatch:
            term_notes.append(_("Selected final delivery term: %s") % self.final_incoterm_id.name)
        
        if term_notes:
            term_info['term_mismatch_notes'] = '\n'.join(term_notes)
        
        # Update the destination picking
        dest_picking.write(term_info)
        
        # Confirm and assign the destination picking
        if dest_picking.state == 'draft':
            dest_picking.action_confirm()
        dest_picking.action_assign()
        
        # Display the destination picking
        return {
            'name': _('Merged Delivery Order'),
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': dest_picking.id,
            'type': 'ir.actions.act_window',
        }
