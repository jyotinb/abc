from odoo import models, fields, api
from odoo.exceptions import ValidationError

class LengthMaster(models.Model):
    _name = 'length.master'
    _description = 'Length Master'
    _order = 'length_value'
    
    length_value = fields.Float('Length Value (m)', required=True)
    description = fields.Text('Description')
    active = fields.Boolean('Active', default=True)
    
    # Related field options for easy selection
    field_option_ids = fields.One2many('length.field.option', 'length_master_id', string='Field Options')
    
    @api.constrains('length_value')
    def _check_positive_length(self):
        for record in self:
            if record.length_value <= 0:
                raise ValidationError('Length value must be positive.')
    
    _sql_constraints = [
        ('unique_length_value', 
         'unique(length_value)', 
         'A length master with this value already exists.'),
        ('positive_length_value', 
         'check(length_value > 0)', 
         'Length value must be positive.')
    ]
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        
        domain = args.copy()
        if name:
            # Search by length value (convert name to float if possible)
            try:
                float_name = float(name)
                domain += [('length_value', operator, float_name)]
            except ValueError:
                # If not a number, search in description
                domain += [('description', operator, name)]
        
        records = self.search(domain, limit=limit)
        return records.name_get()
    
    
    @api.depends('length_value')
    def _compute_display_name(self):
        for record in self:
            record.display_name = str(record.length_value) + 'm'

    def name_get(self):
        self._compute_display_name()
        return super(LengthMaster, self).name_get()
    

class LengthFieldOption(models.Model):
    _name = 'length.field.option'
    _description = 'Length Field Option'
    
    length_master_id = fields.Many2one('length.master', string='Length Master', required=True, ondelete='cascade')
    field_name = fields.Char('Field Name', required=True, 
                            help="Technical field name in green.master model")
    display_name = fields.Char('Display Name', required=True,
                              help="Human-readable field name")
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.display_name} ({record.length_master_id.length_value}m)"
            result.append((record.id, name))
        return result