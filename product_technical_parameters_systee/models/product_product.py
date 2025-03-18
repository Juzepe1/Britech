from odoo import models, fields, api

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.depends('product_tmpl_id.ptp_value_unit_combined')
    def _update_description_sale(self):
        """ Zajišťuje, že description_sale vždy začíná hodnotou ptp_value_unit_combined, ale uživatelský text zůstane zachován """
        for rec in self:
            # Správně získáme hodnotu z product.template
            ptp_value = rec.product_tmpl_id.ptp_value_unit_combined or ""

            if ptp_value:
                existing_description = rec.description_sale or ""

                # Pokud `description_sale` už začíná `ptp_value_unit_combined`, nic se nemění
                if existing_description.startswith(ptp_value):
                    continue

                # Odstranění předchozího `ptp_value_unit_combined`, pokud tam bylo
                parts = existing_description.split("\n", 1)  # Rozdělení textu na první řádek a zbytek
                user_text = parts[1] if len(parts) > 1 else ""

                # Nové description_sale s aktuálním ptp_value_unit_combined
                rec.description_sale = f"{ptp_value}\n{user_text}".strip()

    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        if 'product_tmpl_id' in vals or 'product_tmpl_id.ptp_value_unit_combined' in vals:
            self._update_description_sale()
        return res