# -*- coding: utf-8 -*-

from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = 'product.category'

    ptp_component_type = fields.Char(string="Component Type")
