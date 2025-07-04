# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SymbolLibrary(models.Model):
    _name = 'greenhouse.symbol.library'
    _description = 'Greenhouse & Agriculture Symbol Library'
    _order = 'category, name'

    name = fields.Char('Symbol Name', required=True)
    symbol = fields.Char('Symbol/Emoji', required=True, size=10)
    category = fields.Selection([
        ('plants', 'Plants & Flowers'),
        ('vegetables', 'Vegetables & Fruits'),
        ('tools', 'Farming Tools'),
        ('weather', 'Weather & Climate'),
        ('greenhouse', 'Greenhouse Structures'),
        ('automation', 'Agricultural Automation'),
        ('seasons', 'Seasons & Growth'),
        ('animals', 'Farm Animals'),
        ('environment', 'Environment & Ecology'),
        ('technology', 'Smart Farming Tech'),
        ('certification', 'Organic & Certifications'),
        ('business', 'Business & Marketing'),
    ], string='Category', required=True)
    
    description = fields.Text('Description')
    usage_context = fields.Text('Usage Context')
    active = fields.Boolean('Active', default=True)
    
    # Professional features
    is_seasonal = fields.Boolean('Seasonal Symbol')
    season_type = fields.Selection([
        ('spring', 'Spring'),
        ('summer', 'Summer'),
        ('fall', 'Fall/Autumn'),
        ('winter', 'Winter'),
        ('year_round', 'Year Round'),
    ], string='Season')
    
    business_context = fields.Selection([
        ('b2b', 'Business to Business'),
        ('b2c', 'Business to Consumer'),
        ('both', 'Both B2B & B2C'),
    ], string='Business Context', default='both')
    
    def get_symbols_by_category(self, category):
        """Get all symbols for a specific category"""
        return self.search([('category', '=', category), ('active', '=', True)])
    
    def get_seasonal_symbols(self, season):
        """Get symbols for specific season"""
        return self.search([
            ('is_seasonal', '=', True),
            ('season_type', '=', season),
            ('active', '=', True)
        ])
    
    @api.model
    def get_greenhouse_symbol_categories(self):
        """Get all symbol categories with counts"""
        categories = {}
        for category in self._fields['category'].selection:
            count = self.search_count([('category', '=', category[0]), ('active', '=', True)])
            categories[category[0]] = {
                'name': category[1],
                'count': count,
                'symbols': self.search([('category', '=', category[0]), ('active', '=', True)])
            }
        return categories
