from odoo import models, fields, api

class ProductCategory(models.Model):
    _inherit = 'product.category'

    ptp_systee_component_type = fields.Selection([
        ('capacitor', 'Capacitor'),
        ('resistor', 'Resistor'),
        ('other', 'Other'),
    ], string='Component Type', required=False)

    def write(self, vals):
        """
        Když se v kategorii změní ptp_systee_component_type,
        vyhledáme všechny produkty této kategorie a smažeme jim
        pole nepatřící k novému typu (capacitor/resistor).
        """
        # Uložíme si staré hodnoty typu před zápisem
        old_types = {cat.id: cat.ptp_systee_component_type for cat in self}

        # Zavoláme původní write, čímž dojde ke změně typu
        res = super(ProductCategory, self).write(vals)

        # Pokud se mění typ, musíme upravit produkty
        if 'ptp_systee_component_type' in vals:
            for cat in self:
                new_type = cat.ptp_systee_component_type
                old_type = old_types[cat.id]
                # Pokud je nový typ jiný než starý, vymažeme nepotřebná data
                if new_type != old_type:
                    products = self.env['product.template'].search([('categ_id', '=', cat.id)])
                    products._clear_fields_for_type(new_type)

        return res
