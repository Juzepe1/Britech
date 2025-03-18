from odoo import models, fields, api

class ProductProduct(models.Model):
    _inherit = 'product.product'

    description_sale = fields.Text("Sales Description")
    ptp_value_unit_combined = fields.Char("Value Unit Combined", compute="_compute_value_unit_combined", store=True)

    @api.depends('ptp_value_unit_combined')
    def _update_description_sale(self):
        """ Zajišťuje, že description_sale vždy začíná hodnotou ptp_value_unit_combined, ale uživatelský text zůstane zachován """
        for rec in self:
            if rec.ptp_value_unit_combined:
                existing_description = rec.description_sale or ""
                
                # Pokud `description_sale` už začíná `ptp_value_unit_combined`, nic nedělej
                if existing_description.startswith(rec.ptp_value_unit_combined):
                    continue

                # Odstranění předchozího `ptp_value_unit_combined`, pokud tam bylo
                parts = existing_description.split("\n", 1)  # Rozdělení textu na první řádek a zbytek
                user_text = parts[1] if len(parts) > 1 else ""

                # Nové description_sale s aktuálním ptp_value_unit_combined
                rec.description_sale = f"{rec.ptp_value_unit_combined}\n{user_text}".strip()