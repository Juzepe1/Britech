# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    # Tento modul byl automaticky sestaven podle Excel specifikace, každá komponenta má vlastní prefix podle sloupce B

    categ_component_type = fields.Selection(related='categ_id.ptp_component_type', store=True, readonly=True, string='Typ komponenty kategorie')

class ProductCategory(models.Model):
    _inherit = 'product.category'

    ptp_component_type = fields.Selection([
    ('ant', 'Antény'),
    ('bat', 'Baterie a články'),
    ('bip', 'Bipolární tranzistory'),
    ('blu', 'Bluetooth a wifi'),
    ('cap', 'Kondenzátory'),
    ('chl', 'Chladiče'),
    ('cry', 'Krystaly'),
    ('dio', 'Diody'),
    ('dis', 'Displeje'),
    ('dps', 'Desky plošných spojů'),
    ('drb', 'Držáky baterií'),
    ('drp', 'Držáky pojistek'),
    ('fer', 'Ferity'),
    ('hdd', 'HDD/SSD'),
    ('imp', 'Feritové perličky'),
    ('ind', 'Induktory'),
    ('int', 'Integrované obvody'),
    ('lad', 'Laserové diody'),
    ('led', 'LED diody'),
    ('mas', 'Maskovací pásky'),
    ('nap', 'Napájecí konektory'),
    ('oth', 'Ostatní'),
    ('pas', 'Pájecí pasty a tavidla'),
    ('pin', 'Pinové lišty'),
    ('plc', 'PLC prvky'),
    ('poj', 'Pojistky'),
    ('res', 'Rezistory'),
    ('sab', 'Šablony'),
    ('sch', 'Schottkyho diody'),
    ('sen', 'Senzory'),
    ('tla', 'Tlačítka a přepínače'),
    ('tvs', 'TVS diody'),
    ('tyr', 'Tyristory'),
    ('uni', 'Unipolární tranzistory'),
    ('usb', 'USB konektory'),
    ('usm', 'Usměrňovací diody'),
    ('var', 'Varistory'),
    ('zas', 'Zásuvky a zástrčky'),
    ('zen', 'Zenerovy diody'),
    ], string='Component Type', required=False)

    @api.onchange('ptp_component_type')
    def _onchange_ptp_component_type(self):
        """
        Automaticky předvyplní zkratku do pole ptp_code, pokud je prázdné.
        """
        for record in self:
            if record.ptp_component_type and not record.ptp_code:
                record.ptp_code = record.ptp_component_type[:3].upper()

    ptp_code = fields.Char(string="Category Code", help="Short code for product category")

    @api.constrains('ptp_component_type', 'ptp_code')
    def _check_ptp_code_required(self):
        for record in self:
            if record.ptp_component_type and not record.ptp_code:
                raise ValidationError("Pokud je vyplněno 'Component Type', musí být také vyplněno 'Category Code'.")

    @api.constrains('ptp_component_type')
    def _check_products_before_change(self):
        for record in self:
            if record.ptp_component_type:
                existing_products = self.env['product.template'].search_count([('categ_id', '=', record.id)])
                if existing_products > 0:
                    raise ValidationError("Nelze změnit 'Component Type', protože kategorie obsahuje produkty.")

    def write(self, vals):
        if 'ptp_component_type' in vals:
            for record in self:
                if record.ptp_component_type and record.env['product.template'].search_count([('categ_id', '=', record.id)]) > 0:
                    raise ValidationError("Nelze změnit 'Component Type', protože kategorie obsahuje produkty.")
        return super().write(vals)

    @api.constrains('ptp_code')
    def _check_unique_ptp_code(self):
        for record in self:
            if record.ptp_code:
                existing = self.env['product.category'].search([
                    ('ptp_code', '=', record.ptp_code),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError("Category Code must be unique!")


