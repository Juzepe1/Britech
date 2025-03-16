from odoo import models, fields, api

class ProductCategory(models.Model):
    _inherit = 'product.category'

    ptp_component_type = fields.Selection([
        ('capacitor', 'Capacitor'),
        ('resistor', 'Resistor'),
        ('ferrite_bead', 'Ferrite Bead'),
        ('inductor', 'Inductor'),
        ('transistor', 'Transistor'),
        ('tvs_diode', 'TVS Diode'),
        ('led', 'LED'),
        ('other', 'Other'),
    ], string='Component Type', required=False)

    ptp_code = fields.Char(string="Category Code", help="Short code for product category")

    @api.constrains('ptp_component_type', 'ptp_code')
    def _check_ptp_code_required(self):
        """
        Ověří, že pokud je vyplněno `ptp_component_type`, musí být také vyplněno `ptp_code`.
        """
        for record in self:
            if record.ptp_component_type and not record.ptp_code:
                raise ValidationError("Pokud je vyplněno 'Component Type', musí být také vyplněno 'Category Code'.")

    @api.constrains('ptp_component_type')
    def _check_products_before_change(self):
        """
        Zabrání změně `ptp_component_type`, pokud kategorie obsahuje produkty.
        """
        for record in self:
            if record.ptp_component_type:
                existing_products = self.env['product.template'].search_count([('categ_id', '=', record.id)])
                if existing_products > 0:
                    raise ValidationError("Nelze změnit 'Component Type', protože kategorie obsahuje produkty.")

    def write(self, vals):
        """
        Přepisuje `write`, aby ověřil změny `ptp_component_type` a předešel chybám.
        """
        if 'ptp_component_type' in vals:
            for record in self:
                if record.ptp_component_type and record.env['product.template'].search_count([('categ_id', '=', record.id)]) > 0:
                    raise ValidationError("Nelze změnit 'Component Type', protože kategorie obsahuje produkty.")
        
        return super().write(vals)