# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ContactGroup(models.Model):
    _name = 'email.contact.group'
    _description = 'Email Contact Group'

    name = fields.Char('Group Name', required=True)
    partner_ids = fields.Many2many('res.partner', string='Contacts')
    
    # Greenhouse targeting
    greenhouse_interest = fields.Selection([
        ('general', 'General Interest'),
        ('vegetables', 'Vegetable Growing'),
        ('flowers', 'Flower Production'),
        ('herbs', 'Herb Cultivation'),
        ('organic', 'Organic Farming'),
        ('automation', 'Smart Greenhouse'),
    ], string='Primary Interest')
