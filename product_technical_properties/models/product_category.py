# -*- coding: utf-8 -*-

from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = 'product.category'

    ptp_component_type = fields.Selection([
        ('capacitor', 'Kondenzátor'),
        ('resistor', 'Rezistor'),
        ('other', 'Ostatní')
    ], string="Component Type")
