from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_generate_qr_codes(self):
        """Generate QR codes for all products in the current recordset."""
        return self.env['product.template'].action_generate_qr_codes()
