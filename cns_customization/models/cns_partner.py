from odoo import models, fields, api
from odoo.exceptions import UserError
import re


class CNSPartner(models.Model):
    _inherit = 'res.partner'

    # Name without titles
    cns_name_striped = fields.Char(
        string='Name without titles',
        store=True,
        readonly=True,
    )

    # Datum narození
    cns_datum_narozeni = fields.Date(string='Datum narození')

    # Pobočka
    cns_pobocka = fields.Selection(
        selection=[
            ('2', 'Brno'),
            ('4', 'Česká Lípa'),
            ('5', 'České Budějovice'),
            ('6', 'Domažlice'),
            ('7', 'Habartov'),
            ('8', 'Havířov'),
            ('9', 'Hradec Králové'),
            ('10', 'Cheb'),
            ('11', 'Chomutov'),
            ('12', 'Jihlava'),
            ('13', 'Karviná'),
            ('14', 'Kladno'),
            ('15', 'Kroměřž'),
            ('16', 'Liberec - Jablonec'),
            ('17', 'Louny'),
            ('18', 'Mladá Boleslav'),
            ('19', 'Náchod'),
            ('20', 'Nymburk - Poděbrady'),
            ('21', 'Olomouc'),
            ('22', 'Opava'),
            ('23', 'Ostrava'),
            ('24', 'Papírová platidla'),
            ('25', 'Pardubice'),
            ('27', 'Plzeň'),
            ('1', 'Praha'),
            ('3', 'Pražské groše'),
            ('28', 'Příbor'),
            ('29', 'Příbram'),
            ('30', 'Šumperk'),
            ('31', 'Tábor'),
            ('32', 'Teplice'),
            ('33', 'Turnov'),
            ('34', 'Uherské Hradiště'),
            ('35', 'Ústí nad Labem'),
            ('36', 'Ústí nad Orlicí'),
            ('37', 'Ústředí'),
            ('38', 'Vsetín'),
            ('39', 'Zlín')
        ],
        string='Pobočka'
    )

    cns_clenem_od_roku = fields.Integer(string='Členem od roku')
    cns_zaslat_nc_neclenovi = fields.Boolean(string='Zasílat NČ nečlenovi')
    cns_cestny_clen = fields.Boolean(string='Čestný člen')
    cns_je_ukonceno_clenstvi = fields.Boolean(string='Ukončené členství')

    # Členství v letech
    clenem_v_2019 = fields.Boolean(string='Členem v 2019')
    clenem_v_2020 = fields.Boolean(string='Členem v 2020')
    clenem_v_2021 = fields.Boolean(string='Členem v 2021')
    clenem_v_2022 = fields.Boolean(string='Členem v 2022')
    clenem_v_2023 = fields.Boolean(string='Členem v 2023')
    clenem_v_2024 = fields.Boolean(string='Členem v 2024')
    clenem_v_2025 = fields.Boolean(string='Členem v 2025')
    clenem_v_2026 = fields.Boolean(string='Členem v 2026')
    clenem_v_2027 = fields.Boolean(string='Členem v 2027')
    clenem_v_2028 = fields.Boolean(string='Členem v 2028')
    clenem_v_2029 = fields.Boolean(string='Členem v 2029')
    clenem_v_2030 = fields.Boolean(string='Členem v 2030')
    clenem_v_2031 = fields.Boolean(string='Členem v 2031')
    clenem_v_2032 = fields.Boolean(string='Členem v 2032')

    # Dodací adresa
    delivery_street = fields.Char(string='Ulice dod.', compute='_compute_delivery_address', store=True)
    delivery_street2 = fields.Char(string='Ulice2 dod.', compute='_compute_delivery_address', store=True)
    delivery_city = fields.Char(string='Město dod.', compute='_compute_delivery_address', store=True)
    delivery_zip = fields.Char(string='PSČ dod.', size=24, compute='_compute_delivery_address', store=True)
    delivery_state_id = fields.Many2one('res.country.state', string='Stát dod.', compute='_compute_delivery_address', store=True)
    delivery_country_id = fields.Many2one('res.country', string='Země dod.', compute='_compute_delivery_address', store=True)

    # Číslo člena
    cns_cislo_clena_text = fields.Char(string='Číslo člena', copy=False)

    @staticmethod
    def _remove_titles(name):
        if not name:
            return name
        titles = [
            r"Ing\.", r"Mgr\.", r"Bc\.", r"PhDr\.", r"JUDr\.", r"MUDr\.", r"RNDr\.",
            r"prof\.", r"doc\.", r"Ph\.D\.", r"CSc\.", r"Dr\.", r"MBA", r"DiS\.",
            r"ThDr\.", r"ThLic\.", r"PaedDr\."
        ]
        pattern = r"(?i)^(?:" + "|".join(titles) + r")\s+|" + r"\s+(?:" + "|".join(titles) + r")$"
        cleaned = re.sub(pattern, '', name).strip()
        while re.search(pattern, cleaned):
            cleaned = re.sub(pattern, '', cleaned).strip()
        return cleaned

    def _set_cislo(self, vals):
        if not vals.get('cns_cislo_clena_text') and vals.get('cns_clenem_od_roku'):
            vals['cns_cislo_clena_text'] = self.env['ir.sequence'].next_by_code('res.partner.cislo.clena')
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals = self._set_cislo(vals)
            if vals.get('name'):
                vals['cns_name_striped'] = self._remove_titles(vals['name'])
        return super().create(vals_list)

    def write(self, vals):
        for partner in self:
            if 'name' in vals:
                vals['cns_name_striped'] = partner._remove_titles(vals['name'])

            if not vals.get('cns_cislo_clena_text') and vals.get('cns_clenem_od_roku'):
                vals['cns_cislo_clena_text'] = partner.env['ir.sequence'].next_by_code('res.partner.cislo.clena')

            if vals.get('cns_cislo_clena_text'):
                duplicate = partner.env['res.partner'].search([
                    ('id', '!=', partner.id),
                    ('cns_cislo_clena_text', '=', vals['cns_cislo_clena_text'])
                ], limit=1)
                if duplicate:
                    raise UserError('Číslo člena musí být unikátní.')

        return super().write(vals)

    @api.depends('child_ids', 'child_ids.type', 'child_ids.street', 'child_ids.street2', 'child_ids.city',
                 'child_ids.zip', 'child_ids.state_id', 'child_ids.country_id')
    def _compute_delivery_address(self):
        for partner in self:
            delivery = partner.child_ids.filtered(lambda r: r.type == 'delivery')
            delivery_partner = delivery[0] if delivery else partner
            partner.delivery_street = delivery_partner.street
            partner.delivery_street2 = delivery_partner.street2
            partner.delivery_city = delivery_partner.city
            partner.delivery_zip = delivery_partner.zip
            partner.delivery_state_id = delivery_partner.state_id
            partner.delivery_country_id = delivery_partner.country_id
