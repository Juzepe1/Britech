from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = 'product.category'

    ptp_systee_component_type = fields.Selection([
        ('capacitor', 'Capacitor'),
        ('resistor', 'Resistor'),
        ('other', 'Other'),
    ], string='Component Type', required=False)

    def write(self, vals):
        # Uložíme si staré typy před zápisem
        old_types = {cat.id: cat.ptp_systee_component_type for cat in self}

        # Zavoláme původní write, čímž dojde k zápisu nových hodnot
        res = super().write(vals)

        # Pokud je v `vals` změna ptp_systee_component_type, musíme
        # vymazat stará data u produktů této kategorie
        if 'ptp_systee_component_type' in vals:
            for cat in self:
                new_type = cat.ptp_systee_component_type
                old_type = old_types[cat.id]
                if new_type != old_type:
                    # Najdeme produkty, které mají tuto kategorii
                    products = self.env['product.template'].search([('categ_id', '=', cat.id)])
                    # Zavoláme pomocnou metodu pro vymazání nepotřebných polí
                    products._clear_fields_for_type(new_type)

        return res