from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = 'product.category'

    ptp_systee_component_type = fields.Selection([
        ('capacitor', 'Capacitor'),
        ('resistor', 'Resistor'),
        ('other', 'Other'),
    ], string='Component Type', required=False)
