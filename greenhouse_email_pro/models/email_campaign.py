# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EmailCampaign(models.Model):
    _name = 'email.marketing.campaign'
    _description = 'Email Marketing Campaign'
    _order = 'create_date desc'

    name = fields.Char('Campaign Name', required=True)
    template_id = fields.Many2one('email.marketing.template', string='Template', required=True)
    
    # Campaign metrics
    open_rate = fields.Float('Open Rate %', readonly=True)
    click_rate = fields.Float('Click Rate %', readonly=True)
    
    # Campaign status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('completed', 'Completed'),
    ], default='draft', string='Status')
    
    # Greenhouse specific - FIXED: Using Selection field to match template field type
    greenhouse_category = fields.Selection([
        ('general', 'General Greenhouse'),
        ('vegetables', 'Vegetable Growing'),
        ('flowers', 'Flower Production'),
        ('herbs', 'Herb Cultivation'),
        ('organic', 'Organic Farming'),
        ('hydroponic', 'Hydroponic Systems'),
        ('automation', 'Smart Greenhouse'),
        ('nursery', 'Plant Nursery'),
        ('retail', 'Garden Center'),
        ('wholesale', 'Wholesale Grower'),
    ], string='Greenhouse Category', related='template_id.greenhouse_category', store=True)
    
    growing_season = fields.Selection([
        ('spring', 'Spring Planting'),
        ('summer', 'Summer Growing'),
        ('fall', 'Fall Harvest'),
        ('winter', 'Winter Prep'),
        ('year_round', 'Year Round'),
    ], string='Growing Season', related='template_id.growing_season', store=True)