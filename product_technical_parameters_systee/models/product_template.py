from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

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
    ptp_package = fields.Char(string="Pouzdro")
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
        string='Full Value and Unit',
        compute='_compute_value_unit_combined',
        store=True,
        index=True
    )

    @api.depends(
        'categ_id.ptp_component_type',
        'ptp_cap_value', 'ptp_cap_unit', 'ptp_cap_voltage_rating','ptp_cap_dielectric', 'ptp_cap_tolerance',
        'ptp_res_value', 'ptp_res_unit', 'ptp_res_power_rating', 'ptp_res_tolerance', 'ptp_res_voltage_rating',
        'ptp_package', 'ptp_imp_value', 'ptp_imp_unit',
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

            # Zjistíme, jaká pole jsou pro kategorii relevantní
            category_type = rec.categ_id.ptp_component_type
            ptp_fields = [field for field in rec._fields if field.startswith('ptp_') and not field.endswith('_combined') and not field.endswith('_related') and not field.endswith('_note')]

            # Seznam hodnot, které mají být spojeny
            value_parts = []
            for field_name in ptp_fields:
                field_value = getattr(rec, field_name, False)
                if field_value:
                    # Pokud je pole Many2one (např. jednotky), vezmeme `.name`
                    if isinstance(field_value, models.Model):
                        value_parts.append(field_value.name)
                    else:
                        value_parts.append(str(field_value))

            # Výsledek kombinujeme
            rec.ptp_value_unit_combined = " ".join(value_parts) if value_parts else False

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
                    raise ValidationError("U Jingo je pole 'ptp_part_number' povinné.")
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

    def _generate_product_name(self, vals):
        category = self.categ_id
        if not category or not category.ptp_component_type:
            return vals.get('name', self.name or "").strip()

        default_code = vals.get('default_code', self.default_code or "").strip()
        part_number = vals.get('ptp_part_number', self.ptp_part_number or "").strip()
        existing_name = vals.get('name', self.name or "").strip()

        # Sestavení základního formátu
        base_name = " ".join(filter(None, [default_code, part_number])).strip()

        name_parts = existing_name.split()
        name_parts = [part for part in name_parts if not part.startswith("ITM-")]  # Odebereme starý default_code
        new_name = " ".join([base_name] + name_parts).strip()  # Přidáme nový base_name na začátek

        return new_name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            category_id = vals.get('categ_id')
            category = self.env['product.category'].browse(category_id) if category_id else None

            category_code = category.ptp_code if category and category.ptp_code else '000'
            sequence = self.env['ir.sequence'].next_by_code('product.template.default_code')
            vals['default_code'] = f'ITM-{category.ptp_code}-{sequence}'
            _logger.info(f"Generated default_code: {vals['default_code']}")

            vals['name'] = self._generate_product_name(vals)

        return super().create(vals_list)

    def write(self, vals):
        if 'categ_id' in vals:
            category = self.env['product.category'].browse(vals['categ_id'])
            category_code = category.ptp_code if category and category.ptp_code else '000'

            for record in self:
                if record.default_code:
                    # Aktualizace pouze části s kódem kategorie, zachování sekvenčního čísla
                    parts = record.default_code.split('-')
                    if len(parts) == 3:
                        vals['default_code'] = f'ITM-{category_code}-{parts[2]}'
                    else:
                        vals['default_code'] = f'ITM-{category_code}-{record.default_code}'

                    _logger.info(f"Updated default_code: {vals['default_code']}")
                else:
                    # Pokud `default_code` ještě neexistuje, vytvoří se nový celý
                    sequence = self.env['ir.sequence'].next_by_code('product.template.default_code')
                    vals['default_code'] = f'ITM-{category_code}-{sequence}'
                    _logger.info(f"Generated new default_code: {vals['default_code']}")

        if 'default_code' in vals or 'ptp_part_number' in vals or 'name' in vals:
            vals['name'] = self._generate_product_name(vals)

        return super().write(vals)

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


