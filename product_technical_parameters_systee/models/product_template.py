from odoo import models, fields, api
from odoo.exceptions import ValidationError

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

    ptp_systee_category_type_related = fields.Selection(
        related='categ_id.ptp_systee_component_type',
        string='Category Type (related)',
        store=False  # nepotřebujeme ukládat do DB
    )

    # Společná pole
    ptp_systee_part_number = fields.Char(string='Part Number')
    ptp_systee_footprint = fields.Selection(
        [
            ('0201', '0201'),
            ('0402', '0402'),
            ('0603', '0603'),
            ('0805', '0805'),
            ('1206', '1206'),
            ('1210', '1210'),
            ('1216', '1216'),
            ('2010', '2010'),
            ('1812', '1812'),
            ('2220', '2220'),
        ],
        string='Footprint'
    )
    ptp_systee_note = fields.Text(string='Note')

    # Pole pro kondenzátory
    ptp_systee_cap_value = fields.Char(string='Value (C)')
    ptp_systee_cap_unit = fields.Selection(
        [
        ('pF', 'pF'),
        ('nF', 'nF'),
        ('µF', 'μF'),
        ],
        string='Unit (C)'
    )
    ptp_systee_cap_voltage_rating = fields.Char(string='Voltage Rating [VDC]')
    ptp_systee_cap_dielectric = fields.Selection(
        [
            ('c0g', 'C0G (NP0)'),
            ('x5r', 'X5R'),
            ('x7r', 'X7R'),
            ('x6s', 'X6S'),
            ('x7s', 'X7S'),
            ('x7t', 'X7T'),
        ],
        string='Dielectric'
    )
    ptp_systee_cap_tolerance = fields.Char(string='Tolerance [%]')

    # Pole pro rezistory
    ptp_systee_res_value = fields.Char(string='Value (R)')
    ptp_systee_res_unit = fields.Selection(
        [
            ('mOhm', 'mdfd')
        ],
        string='Unit (R)'
    )
    ptp_systee_res_power_rating = fields.Char(string='Power Rating')
    ptp_systee_res_tolerance = fields.Char(string='Tolerance [%]')
    ptp_systee_res_voltage_rating = fields.Char(string='Voltage Rating [V]')

    # Počítané pole: sloučená hodnota + jednotka
    ptp_systee_value_unit_combined = fields.Char(
        string='Full Value and Unit',
        compute='_compute_value_unit_combined',
        store=True,
        index=True
    )

    @api.depends(
        'categ_id.ptp_systee_component_type',
        'ptp_systee_cap_value', 'ptp_systee_cap_unit',
        'ptp_systee_res_value', 'ptp_systee_res_unit'
    )
    def _compute_value_unit_combined(self):
        for rec in self:
            ctype = rec.categ_id.ptp_systee_component_type
            if ctype == 'capacitor' and rec.ptp_systee_cap_value and rec.ptp_systee_cap_unit:
                rec.ptp_systee_value_unit_combined = f"{rec.ptp_systee_cap_value} {rec.ptp_systee_cap_unit}"
            elif ctype == 'resistor' and rec.ptp_systee_res_value and rec.ptp_systee_res_unit:
                rec.ptp_systee_value_unit_combined = f"{rec.ptp_systee_res_value} {rec.ptp_systee_res_unit}"
            else:
                rec.ptp_systee_value_unit_combined = False

    @api.onchange(
        'ptp_systee_cap_value', 'ptp_systee_cap_tolerance', 'ptp_systee_cap_voltage_rating',
        'ptp_systee_res_value', 'ptp_systee_res_tolerance', 'ptp_systee_res_voltage_rating',
        'ptp_systee_res_power_rating'
    )
    def _onchange_replace_dot_with_comma(self):
        """
        Pokud uživatel zadá desetinnou tečku, automaticky ji nahradíme za čárku.
        """
        fields_to_clean = [
            'ptp_systee_cap_value', 'ptp_systee_cap_tolerance', 'ptp_systee_cap_voltage_rating',
            'ptp_systee_res_value', 'ptp_systee_res_tolerance', 'ptp_systee_res_voltage_rating',
            'ptp_systee_res_power_rating'
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
            rec.ptp_systee_part_number = False
            rec.ptp_systee_footprint = False
            rec.ptp_systee_note = False
            rec.ptp_systee_value_unit_combined = False
            # Není capacitor => vymažeme kondenzátorová pole
            if new_type != 'capacitor':
                rec.ptp_systee_cap_value = False
                rec.ptp_systee_cap_unit = False
                rec.ptp_systee_cap_voltage_rating = False
                rec.ptp_systee_cap_dielectric = False
                rec.ptp_systee_cap_tolerance = False

            # Není resistor => vymažeme rezistorová pole
            if new_type != 'resistor':
                rec.ptp_systee_res_value = False
                rec.ptp_systee_res_unit = False
                rec.ptp_systee_res_power_rating = False
                rec.ptp_systee_res_tolerance = False
                rec.ptp_systee_res_voltage_rating = False

    # --------------------------------------------------------------------------------
    # Onchange: při změně kategorie v detailu produktu 
    # (když uživatel vybere jinou category) => vymažeme nepotřebná data
    # --------------------------------------------------------------------------------
    @api.onchange('categ_id')
    def _onchange_categ_id_clear_fields(self):
        new_type = self.categ_id.ptp_systee_component_type or False
        self._clear_fields_for_type(new_type)

    # --------------------------------------------------------------------------------
    # Validace: zkontroluje jen pole relevantní k finálnímu typu
    # --------------------------------------------------------------------------------
    @api.constrains(
        'ptp_systee_cap_value', 'ptp_systee_cap_unit', 'ptp_systee_cap_voltage_rating',
        'ptp_systee_cap_dielectric', 'ptp_systee_cap_tolerance',
        'ptp_systee_res_value', 'ptp_systee_res_unit', 'ptp_systee_res_power_rating',
        'ptp_systee_res_tolerance', 'ptp_systee_res_voltage_rating', 'ptp_systee_part_number', 'ptp_systee_footprint')

    def _check_required_fields(self):
        for rec in self:
            ctype = rec.categ_id.ptp_systee_component_type
            # Pokud typ není vyplněn (False) nebo je 'other', 
            # žádné speciální validace nepotřebujeme.
            if not ctype:
                continue

            if ctype == 'other':
                # Zde definujte, co je povinné u Other
                if not rec.ptp_systee_part_number:
                    raise ValidationError("U Jingo je pole 'ptp_systee_part_number' povinné.")
                continue

            if ctype == 'capacitor':
                # Zde definujte, co je povinné u kondenzátoru
                if not rec.ptp_systee_part_number:
                    raise ValidationError("U kondenzátoru je pole 'ptp_systee_part_number' povinné.")
                if not rec.ptp_systee_footprint:
                    raise ValidationError("U kondenzátoru je pole 'ptp_systee_footprint' povinné.")
                if not rec.ptp_systee_cap_value:
                    raise ValidationError("U kondenzátoru je pole 'cap_value' povinné.")
                if not rec.ptp_systee_cap_unit:
                    raise ValidationError("U kondenzátoru je pole 'cap_unit' povinné.")
                if not rec.ptp_systee_cap_dielectric:
                    raise ValidationError("U kondenzátoru je pole 'cap_dielectric' povinné.")
                # ... atd. (další logika, např. reálné číslo)

            elif ctype == 'resistor':
                # Zde definujte, co je povinné u rezistoru
                if not rec.ptp_systee_part_number:
                    raise ValidationError("U rezistoru je pole 'ptp_systee_part_number' povinné.")
                if not rec.ptp_systee_footprint:
                    raise ValidationError("U rezistoru je pole 'ptp_systee_footprint' povinné.")
                if not rec.ptp_systee_res_value:
                    raise ValidationError("U rezistoru je pole 'res_value' povinné.")
                if not rec.ptp_systee_res_unit:
                    raise ValidationError("U rezistoru je pole 'res_unit' povinné.")
                # ... atd.