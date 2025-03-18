from odoo import models, fields, api

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.depends('product_tmpl_id.ptp_value_unit_combined')
    def _compute_description_sale(self):
        """ Automaticky aktualizuje description_sale při změně ptp_value_unit_combined """
        for rec in self:
            ptp_value = rec.product_tmpl_id.ptp_value_unit_combined or ""

            if ptp_value:
                existing_description = rec.description_sale or ""

                # Pokud `description_sale` už začíná `ptp_value_unit_combined`, neaktualizujeme
                if existing_description.startswith(ptp_value):
                    continue

                # Rozdělení popisu, abychom zachovali uživatelský text
                parts = existing_description.split("\n", 1)
                user_text = parts[1] if len(parts) > 1 else ""

                # Aktualizace popisu
                rec.description_sale = f"{ptp_value}\n{user_text}".strip()

    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        if 'product_tmpl_id' in vals or 'product_tmpl_id.ptp_value_unit_combined' in vals:
            self._update_description_sale()
        return res