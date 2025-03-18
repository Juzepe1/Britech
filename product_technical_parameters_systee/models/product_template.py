from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
import base64
import qrcode
from io import BytesIO

_logger = logging.getLogger(__name__)

def is_float_or_dash(val):
    """
    Vrátí True, pokud je hodnota prázdná, '-' nebo konvertovatelná na float
    (s možným nahrazením čárky za tečku).
    """
    if not val or val.strip() == '-':
        return True
    try:
        float(val.replace(',', '.'))
        return True
    except ValueError:
        return False


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    qr_code = fields.Binary("QR Code", compute="_generate_qr_code", store=True)

    ptp_sequence_number = fields.Integer(string="Product Sequence", readonly=True)


    ptp_category_type_related = fields.Selection(
        related='categ_id.ptp_component_type',
        string='Category Type (related)',
        store=False  # nepotřebujeme ukládat do DB
    )

    # Společná pole
    ptp_part_number = fields.Char(string='Part Number')
    ptp_footprint = fields.Many2one(
        'ptp.footprint',
        string='Footprint'
    )
    ptp_note = fields.Text(string='Note')

    # Pole pro kondenzátory
    ptp_cap_value = fields.Char(string='Value (C)')
    ptp_cap_unit = fields.Many2one(
        'ptp.cap.unit',
        string='Unit (C)'
    )
    ptp_cap_voltage_rating = fields.Char(string='Voltage Rating [VDC]')
    ptp_cap_dielectric = fields.Many2one(
        'ptp.cap.dielectric',
        string='Dielectric'
    )
    ptp_cap_tolerance = fields.Char(string='Tolerance [%]')

    # Pole pro rezistory
    ptp_res_value = fields.Char(string='Value (R)')
    ptp_res_unit = fields.Many2one(
        'ptp.res.unit',
        string='Unit (R)'
    )
    ptp_res_power_rating = fields.Char(string='Power Rating')
    ptp_res_tolerance = fields.Char(string='Tolerance [%]')
    ptp_res_voltage_rating = fields.Char(string='Voltage Rating [V]')

    # Pole pro Feritové perličky
    ptp_imp_value = fields.Char(string="Impedance")
    ptp_imp_unit = fields.Many2one(
        'ptp.imp.unit',
        string='Unit (Z)'
    )
    # Pole pro Induktory
    ptp_ind_value = fields.Char(string="Induktance")
    ptp_ind_unit = fields.Many2one(
        'ptp.ind.unit',
        string='Unit (X)'
    )

    # Pole pro Tranzistory
    ptp_tran_polarity = fields.Many2one(
        'ptp.tran.polarity',
        string='Tranzistor polarity'
    )
    ptp_tran_type = fields.Many2one(
        'ptp.tran.type',
        string='Tranzistor typ'
    )

    # Pole pro TVS diody
    ptp_tvs_polarity = fields.Many2one(
        'ptp.tvs.polarity',
        string='TVS dioda polarity'
    )
    ptp_tvs_chanel = fields.Many2one(
        'ptp.tvs.chanel',
        string='TVS dioda počet kanálů'
    )

    # Pole pro LED
    ptp_led_color = fields.Many2one(
        'ptp.led.color',
        string='LED barva'
    )

    # Počítané pole: sloučená hodnota + jednotka
    ptp_value_unit_combined = fields.Char(
        string='Description',
        compute='_compute_value_unit_combined',
        store=True,
        index=True
    )

    @api.depends('default_code')
    def _compute_qr_code(self):
        """ Automaticky generuje QR kód při změně `default_code`. """
        for rec in self:
            if rec.default_code:
                rec.qr_code = rec._generate_qr_code()
            else:
                rec.qr_code = False  # Pokud není `default_code`, QR kód smažeme

    def _generate_qr_code(self):
        """ Generuje QR kód pro tento konkrétní produkt """
        if not self.default_code:
            return False

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.default_code)
        qr.make(fit=True)

        img = qr.make_image(fill='black', back_color='white')
        temp = BytesIO()
        img.save(temp, format="PNG")
        return base64.b64encode(temp.getvalue())

    def generate_missing_qr_codes(self):
        """ Najde produkty bez QR kódu, které mají `default_code`, a vygeneruje pro ně QR """
        products = self.search([('default_code', '!=', False), ('qr_code', '=', False)])
        for product in products:
            product.qr_code = product._generate_qr_code()  # Opravené volání na instanci

    def action_generate_qr_codes(self):
        """ Akce tlačítka - generování QR kódů pro všechny produkty bez QR """
        self.generate_missing_qr_codes()
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'QR kódy byly úspěšně vygenerovány!',
                'type': 'rainbow_man',
            }
        }

    @api.depends('ptp_value_unit_combined')
    def _compute_description_sale(self):
        """ Automaticky aktualizuje `description_sale` při změně `ptp_value_unit_combined` """
        for rec in self:
            # Použijeme přímý přístup na pole místo cache
            ptp_value = rec.ptp_value_unit_combined or ""

            if ptp_value:
                existing_description = rec.description_sale or ""

                # Pokud `description_sale` už začíná `ptp_value_unit_combined`, neaktualizujeme
                if existing_description.startswith(ptp_value):
                    continue

                # Rozdělení popisu na první řádek (kombinovaná hodnota) a zbytek (uživatelský text)
                parts = existing_description.split("\n", 1)
                user_text = parts[1] if len(parts) > 1 else ""

                # Aktualizace popisu
                rec.description_sale = f"{ptp_value}\n{user_text}".strip()

    @api.depends(
        'categ_id.ptp_component_type',
        'ptp_cap_value', 'ptp_cap_unit', 'ptp_cap_voltage_rating','ptp_cap_dielectric', 'ptp_cap_tolerance',
        'ptp_res_value', 'ptp_res_unit', 'ptp_res_power_rating', 'ptp_res_tolerance', 'ptp_res_voltage_rating',
        'ptp_imp_value', 'ptp_imp_unit',
        'ptp_ind_value', 'ptp_ind_unit',
        'ptp_tran_polarity', 'ptp_tran_type',
        'ptp_tvs_polarity', 'ptp_tvs_chanel',
        'ptp_led_color'
    )
    def _compute_value_unit_combined(self):
        for rec in self:
            if not rec.categ_id:
                rec.ptp_value_unit_combined = False
                continue

            category_type = getattr(rec.categ_id, "ptp_component_type", "")
            value_unit_map = {
                'capacitor': [
                    ('ptp_part_number', None),
                    ('ptp_cap_value', 'ptp_cap_unit'),
                    ('ptp_cap_voltage_rating', 'V'),
                    ('ptp_cap_dielectric', None),
                    ('ptp_cap_tolerance', '%'),
                ],
                'resistor': [
                    ('ptp_part_number', None),
                    ('ptp_res_value', 'ptp_res_unit'),
                    ('ptp_res_power_rating', 'W'),
                    ('ptp_res_voltage_rating', 'V'),
                    ('ptp_res_tolerance', '%'),
                ],
                'ferrite_bead': [
                    ('ptp_part_number', None),
                    ('ptp_imp_value', 'ptp_imp_unit'),
                ],
                'inductor': [
                    ('ptp_part_number', None),
                    ('ptp_ind_value', 'ptp_ind_unit'),
                ],
                'transistor': [
                    ('ptp_part_number', None),
                    ('ptp_tran_polarity', None),
                    ('ptp_tran_type', None),
                ],
                'tvs_diode': [
                    ('ptp_part_number', None),
                    ('ptp_tvs_polarity', None),
                    ('ptp_tvs_chanel', None),
                ],
                'led': [
                    ('ptp_part_number', None),
                    ('ptp_led_color', None),
                ],
            }

            combined_values = []
            if category_type in value_unit_map:
                for value_field, unit_field in value_unit_map[category_type]:
                    value = getattr(rec, value_field, "") or ""
                    unit_name = ""

                    # Získání správné jednotky
                    if unit_field:
                        unit = getattr(rec, unit_field, False)
                        if unit and hasattr(unit, "name"):  # Kontrola, zda má `.name`
                            unit_name = unit.name or ""
                        elif isinstance(unit_field, str):  # Pevně definované jednotky ('V', 'W', '%')
                            unit_name = unit_field

                    # Pokud je hodnota Many2one, převedeme na `.name`
                    if isinstance(value, models.Model):
                        value = value.name or ""

                    value = str(value).strip()
                    unit_name = str(unit_name).strip()

                    # Správné spojení hodnoty a jednotky
                    if value and unit_name:
                        combined_values.append(f"{value}{unit_name}")
                    elif value:
                        combined_values.append(value)
            # Kombinujeme všechny hodnoty do jednoho řetězce
            rec.ptp_value_unit_combined = " ".join(combined_values) if combined_values else False
        self.env.cr.flush()
        self._compute_description_sale()

    @api.onchange(
        'ptp_cap_value', 'ptp_cap_tolerance', 'ptp_cap_voltage_rating',
        'ptp_res_value', 'ptp_res_tolerance', 'ptp_res_voltage_rating',
        'ptp_res_power_rating'
    )
    def _onchange_replace_dot_with_comma(self):
        """
        Pokud uživatel zadá desetinnou tečku, automaticky ji nahradíme za čárku.
        """
        fields_to_clean = [
            'ptp_cap_value', 'ptp_cap_tolerance', 'ptp_cap_voltage_rating',
            'ptp_res_value', 'ptp_res_tolerance', 'ptp_res_voltage_rating',
            'ptp_res_power_rating'
        ]
        for rec in self:
            for field_name in fields_to_clean:
                val = getattr(rec, field_name)
                if val and val.strip() != '-' and '.' in val:
                    setattr(rec, field_name, val.replace('.', ','))

    # --------------------------------------------------------------------------------
    # Metoda pro vymazání starých dat, která nepatří k novému typu
    # --------------------------------------------------------------------------------
    def _clear_fields_for_type(self, new_type):
        """
        Podle `new_type` smaže pole kondenzátoru / rezistoru, 
        pokud se k novému typu nehodí.
        """
        for rec in self:
            rec.ptp_part_number = False
            rec.ptp_footprint = False
            rec.ptp_note = False
            rec.ptp_value_unit_combined = False
            # Není capacitor => vymažeme kondenzátorová pole
            if new_type != 'capacitor':
                rec.ptp_cap_value = False
                rec.ptp_cap_unit = False
                rec.ptp_cap_voltage_rating = False
                rec.ptp_cap_dielectric = False
                rec.ptp_cap_tolerance = False

            # Není resistor => vymažeme rezistorová pole
            if new_type != 'resistor':
                rec.ptp_res_value = False
                rec.ptp_res_unit = False
                rec.ptp_res_power_rating = False
                rec.ptp_res_tolerance = False
                rec.ptp_res_voltage_rating = False

            # Není ferrite_bead => vymažeme ferrite_bead pole
            if new_type != 'ferrite_bead':
                rec.ptp_imp_value = False
                rec.ptp_imp_unit = False

            # Není inductor => vymažeme inductor pole
            if new_type != 'inductor':
                rec.ptp_ind_value = False
                rec.ptp_ind_unit = False

            # Není transistor => vymažeme transistor pole
            if new_type != 'transistor':
                rec.ptp_tran_polarity = False
                rec.ptp_tran_type = False

            # Není tvs_diode => vymažeme tvs_diode pole
            if new_type != 'tvs_diode':
                rec.ptp_tvs_polarity = False
                rec.ptp_tvs_chanel = False

            # Není led => vymažeme led pole
            if new_type != 'led':
                rec.ptp_led_color = False

    # --------------------------------------------------------------------------------
    # Onchange: při změně kategorie v detailu produktu 
    # (když uživatel vybere jinou category) => vymažeme nepotřebná data
    # --------------------------------------------------------------------------------
    @api.onchange('categ_id')
    def _onchange_categ_id_clear_fields(self):
        new_type = self.categ_id.ptp_component_type or False
        self._clear_fields_for_type(new_type)

    # --------------------------------------------------------------------------------
    # Validace: zkontroluje jen pole relevantní k finálnímu typu
    # --------------------------------------------------------------------------------
    @api.constrains(
        'ptp_cap_value', 'ptp_cap_unit', 'ptp_cap_voltage_rating',
        'ptp_cap_dielectric', 'ptp_cap_tolerance',
        'ptp_res_value', 'ptp_res_unit', 'ptp_res_power_rating',
        'ptp_res_tolerance', 'ptp_res_voltage_rating', 
        'ptp_part_number', 'ptp_footprint'
    )
    def _check_required_fields(self):
        for rec in self:
            ctype = rec.categ_id.ptp_component_type
            # Pokud typ není vyplněn (False) nebo je 'other', 
            # žádné speciální validace nepotřebujeme.
            if not ctype:
                continue

            if ctype == 'other':
                # Zde definujte, co je povinné u Other
                if not rec.ptp_part_number:
                    raise ValidationError("U jingo je pole 'ptp_part_number' povinné.")
                continue

            if ctype == 'capacitor':
                # Zde definujte, co je povinné u kondenzátoru
                if not rec.ptp_part_number:
                    raise ValidationError("U kondenzátoru je pole 'ptp_part_number' povinné.")
                if not rec.ptp_footprint:
                    raise ValidationError("U kondenzátoru je pole 'ptp_footprint' povinné.")
                if not rec.ptp_cap_value:
                    raise ValidationError("U kondenzátoru je pole 'cap_value' povinné.")
                if not rec.ptp_cap_unit:
                    raise ValidationError("U kondenzátoru je pole 'cap_unit' povinné.")
                if not rec.ptp_cap_dielectric:
                    raise ValidationError("U kondenzátoru je pole 'cap_dielectric' povinné.")
                # Další logika validace může následovat...

            elif ctype == 'resistor':
                # Zde definujte, co je povinné u rezistoru
                if not rec.ptp_part_number:
                    raise ValidationError("U rezistoru je pole 'ptp_part_number' povinné.")
                if not rec.ptp_footprint:
                    raise ValidationError("U rezistoru je pole 'ptp_footprint' povinné.")
                if not rec.ptp_res_value:
                    raise ValidationError("U rezistoru je pole 'res_value' povinné.")
                if not rec.ptp_res_unit:
                    raise ValidationError("U rezistoru je pole 'res_unit' povinné.")
                # Další logika validace může následovat...

            elif ctype == 'ferrite_bead':
                # Zde definujte, co je povinné u rezistoru
                if not rec.ptp_part_number:
                    raise ValidationError("U feritu je pole 'ptp_part_number' povinné.")

            elif ctype == 'inductor':
                # Zde definujte, co je povinné u rezistoru
                if not rec.ptp_part_number:
                    raise ValidationError("U induktoru je pole 'ptp_part_number' povinné.")

            elif ctype == 'transistor':
                # Zde definujte, co je povinné u rezistoru
                if not rec.ptp_part_number:
                    raise ValidationError("U tranzistoru je pole 'ptp_part_number' povinné.")

            elif ctype == 'tvs_diode':
                # Zde definujte, co je povinné u rezistoru
                if not rec.ptp_part_number:
                    raise ValidationError("U TVS diod je pole 'ptp_part_number' povinné.")

            elif ctype == 'led':
                # Zde definujte, co je povinné u rezistoru
                if not rec.ptp_part_number:
                    raise ValidationError("U led je pole 'ptp_part_number' povinné.")


    def _ensure_default_code(self, vals, new_sequence=False):
        """
        Vždy vygeneruje `default_code`. Pokud `new_sequence=True`, vytvoří nové číslo sekvence,
        jinak zachová původní číslo sekvence.
        """
        category_id = vals.get('categ_id', self.categ_id.id)
        category = self.env['product.category'].browse(category_id) if category_id else None
        category_code = category.ptp_code if category and category.ptp_code else '000'

        if new_sequence or not self.default_code:
            # **Pokud se jedná o nový produkt, vytvoříme nové číslo sekvence**
            sequence = self.env['ir.sequence'].next_by_code('product.template.default_code')
        else:
            # **Při změně kategorie zachováme číslo sekvence**
            parts = self.default_code.split('-')
            sequence = parts[-1] if len(parts) == 3 else self.default_code

        vals['default_code'] = f'ITM-{category_code}-{sequence}'
        _logger.info(f"Generated default_code: {vals['default_code']}")

    def _ensure_product_name(self, vals):
        """
        Vždy aktualizuje `name` podle `default_code`, aby nedocházelo k duplikacím.
        """
        vals['name'] = self._generate_product_name(vals)

    def _generate_product_name(self, vals):
        """
        Generuje správný název produktu pouze s `ptp_part_number` a dalšími částmi názvu,
        ale bez `default_code`. Zabrání duplicitnímu výskytu `ptp_part_number`.
        """
        part_number = vals.get('ptp_part_number', self.ptp_part_number)
        if not isinstance(part_number, str):  
            part_number = ""  # Pokud je False nebo None, nastavíme prázdný řetězec
        part_number = part_number.strip()
        existing_name = vals.get('name', self.name or "").strip()
    
        # Rozdělíme existující název na části
        name_parts = existing_name.split()
        name_parts = [part for part in name_parts if part != self.ptp_part_number]

        # Pokud `part_number` už v názvu existuje, nebudeme ho přidávat znovu
        if part_number in name_parts:
            new_name = " ".join(name_parts).strip()
        else:
            new_name = " ".join([part_number] + name_parts).strip()

        return new_name

    @api.model_create_multi
    def create(self, vals_list):
        """
        Při vytváření produktu se vždy nastaví `default_code` a `name`.
        """
        for vals in vals_list:
            self._ensure_default_code(vals, new_sequence=True)  # Nové číslo sekvence
            category = self.env['product.category'].browse(vals.get('categ_id')) if vals.get('categ_id') else None
            if category and category.ptp_component_type:
                self._ensure_product_name(vals)
        records = super().create(vals_list)  # Vytvoříme záznamy
        records._check_required_fields()

        return records

    def write(self, vals):

        if 'categ_id' in vals:
            self._ensure_default_code(vals, new_sequence=False)

        new_category = self.env['product.category'].browse(vals['categ_id']) if vals.get('categ_id') else self.categ_id
        if new_category and new_category.ptp_component_type:
            self._ensure_product_name(vals)
        category_changed = 'categ_id' in vals  #  Kontrola, zda se mění kategorie

        if category_changed:
            old_categories = {rec.id: rec.categ_id for rec in self}  # Uložení staré kategorie
            self._ensure_default_code(vals, new_sequence=False)

        result = super().write(vals)
        if 'default_code' in vals:
            self._compute_qr_code()  # Regenerace QR kódu

        if category_changed:
            for record in self:
                old_category = old_categories.get(record.id)
                new_category = record.categ_id

            # Pokud nová kategorie má `ptp_component_type`, validujeme povinná pole
                if new_category and new_category.ptp_component_type:
                    record._check_required_fields()
        return result


# --- Definice referenčních modelů pro many2one pole ---

class PtpFootprint(models.Model):
    _name = 'ptp.footprint'
    _description = 'Systee Footprint'

    name = fields.Char(string="Footprint", required=True)


class PtpCapUnit(models.Model):
    _name = 'ptp.cap.unit'
    _description = 'Capacitor Unit'

    name = fields.Char(string="Unit", required=True)


class PtpCapDielectric(models.Model):
    _name = 'ptp.cap.dielectric'
    _description = 'Capacitor Dielectric'

    name = fields.Char(string="Dielectric", required=True)


class PtpResUnit(models.Model):
    _name = 'ptp.res.unit'
    _description = 'Resistor Unit'

    name = fields.Char(string="Unit", required=True)

class PtpImpUnit(models.Model):
    _name = 'ptp.imp.unit'
    _description = 'Ferrite Bead Unit'

    name = fields.Char(string="Impedance Unit", required=True)

# --- Induktory ---
class PtpIndUnit(models.Model):
    _name = 'ptp.ind.unit'
    _description = 'Inductor Unit'

    name = fields.Char(string="Inductance Unit", required=True)

# --- Tranzistory ---
class PtpTranPolarity(models.Model):
    _name = 'ptp.tran.polarity'
    _description = 'Transistor Polarity'

    name = fields.Char(string="Polarity", required=True)

class PtpTranType(models.Model):
    _name = 'ptp.tran.type'
    _description = 'Transistor Type'

    name = fields.Char(string="Type", required=True)

# --- TVS diody ---
class PtpTvsPolarity(models.Model):
    _name = 'ptp.tvs.polarity'
    _description = 'TVS Diode Polarity'

    name = fields.Char(string="Polarity", required=True)

class PtpTvsChannel(models.Model):
    _name = 'ptp.tvs.chanel'
    _description = 'TVS Diode Channel Count'

    name = fields.Char(string="Channel Count", required=True)

# --- LED ---
class PtpLedColor(models.Model):
    _name = 'ptp.led.color'
    _description = 'LED Color'

    name = fields.Char(string="Color", required=True)


