from odoo import models, fields, api
from odoo.exceptions import UserError


class CNSPartner(models.Model):
    cns_name_striped = fields.Char(string='Name without titles', readonly=True)

    @staticmethod
    def _remove_titles(name):
        if not name:
            return name
        titles = [
            "Ing\.", "Mgr\.", "Bc\.", "PhDr\.", "JUDr\.", "MUDr\.", "RNDr\.", "prof\.", "doc\.",
            "Ph\.D\.", "CSc\.", "Dr\.", "MBA", "DiS\.", "ThDr\.", "ThLic\.", "PaedDr\."
        ]
        import re
        title_pattern = r"(?i)^(?:" + "|".join(titles) + r")\s+|" + r"\s+(?:" + "|".join(titles) + r")$"
        cleaned = re.sub(title_pattern, '', name).strip()
        while re.search(title_pattern, cleaned):
            cleaned = re.sub(title_pattern, '', cleaned).strip()
        return cleaned

    @api.model
    def create(self, vals):
        if 'name' in vals:
            vals['cns_name_striped'] = self._remove_titles(vals['name'])
        return super().create(vals)

    def write(self, vals):
        if 'name' in vals:
            vals['cns_name_striped'] = self._remove_titles(vals['name'])
        return super().write(vals)

    _inherit = 'res.partner'

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

    # Členem od roku
    cns_clenem_od_roku = fields.Integer(string='Členem od roku')

    # Zasílat NČ nečlenovi
    cns_zaslat_nc_neclenovi = fields.Boolean(string='Zasílat NČ nečlenovi')

    # Čestný člen
    cns_cestny_clen = fields.Boolean(string='Čestný člen')

    # Ukončené členství
    cns_je_ukonceno_clenstvi = fields.Boolean(string='Ukončené členství')

    # Generování pole pro každý rok od 2022 do 2032
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

    delivery_street = fields.Char(string='Ulice dod.', compute='_compute_delivery_address', store=True)
    delivery_street2 = fields.Char(string='Ulice2 dod.', compute='_compute_delivery_address', store=True)
    delivery_city = fields.Char(string='Město dod.', compute='_compute_delivery_address', store=True)
    delivery_zip = fields.Char(change_default=True, string='PSČ dod.', size=24, compute='_compute_delivery_address', store=True)
    delivery_state_id = fields.Many2one(string='Stát dod.', comodel_name='res.country.state', compute='_compute_delivery_address', store=True)
    delivery_country_id = fields.Many2one(string='Země dod.', comodel_name='res.country', compute='_compute_delivery_address', store=True)

    # Číslo člena (text) s automatickou sekvencí
    cns_cislo_clena_text = fields.Char(string='Číslo člena', copy=False)

    @api.onchange('street', 'street2', 'city', 'zip', 'state_id', 'country_id')
    @api.depends('child_ids', 'child_ids.type', 'child_ids.street', 'child_ids.street2', 'child_ids.city', 'child_ids.zip', 'child_ids.state_id', 'child_ids.country_id')
    def _compute_delivery_address(self):
        for partner in self:
            if partner.type == 'delivery' and partner.parent_id:
                partner.parent_id._compute_delivery_address()

            if partner.child_ids.filtered(lambda r: r.type == 'delivery'):
                delivery_partner = partner.child_ids.filtered(lambda r: r.type == 'delivery')[0]
                partner.delivery_street = delivery_partner.street
                partner.delivery_street2 = delivery_partner.street2
                partner.delivery_city = delivery_partner.city
                partner.delivery_zip = delivery_partner.zip
                partner.delivery_state_id = delivery_partner.state_id
                partner.delivery_country_id = delivery_partner.country_id
            else:
                partner.delivery_street = partner.street
                partner.delivery_street2 = partner.street2
                partner.delivery_city = partner.city
                partner.delivery_zip = partner.zip
                partner.delivery_state_id = partner.state_id
                partner.delivery_country_id = partner.country_id

    def _set_cislo(self, vals):
        if not vals.get('cns_cislo_clena_text') and vals.get('cns_clenem_od_roku', 0) != 0:
            vals['cns_cislo_clena_text'] = self.env['ir.sequence'].next_by_code('res.partner.cislo.clena')
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [self._set_cislo(item) for item in vals_list]
        return super(CNSPartner, self).create(vals_list)

    @api.model
    def write(self, vals):
        if not vals.get('cns_cislo_clena_text') and vals.get('cns_clenem_od_roku', 0) != 0:
            vals['cns_cislo_clena_text'] = self.env['ir.sequence'].next_by_code('res.partner.cislo.clena')

        if vals.get('cns_cislo_clena_text'):
            if self.env['res.partner'].search([
                ('id', '!=', self.id),
                ('cns_cislo_clena_text', '=', vals.get('cns_cislo_clena_text'))
            ]):
                raise UserError('Číslo člena musí být unikátní.')

        return super(CNSPartner, self).write(vals)
