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
    # Obecná pole 
    qr_code = fields.Binary("QR Code", compute="_generate_qr_code", store=True)
    ptp_sequence_number = fields.Integer(string="Product Sequence", readonly=True)
    ptp_category_type_related = fields.Selection(
        related='categ_id.ptp_component_type',
        string='Category Type (related)',
        store=False  # nepotřebujeme ukládat do DB
    )
    # Počítané pole: sloučená hodnota + jednotka
    ptp_value_unit_combined = fields.Char(
        string='Description',
        compute='_compute_value_unit_combined_desc',
        store=True,
        index=True
    )

    # Společná pole
    ptp_part_number = fields.Char(string='Part Number')
    ptp_footprint = fields.Many2one('ptp.footprint', string='Footprint')
    ptp_note = fields.Text(string='Note')

    # Jednotlivá pole DPS
    ptp_dps_rozmery_value = fields.Char(string='Rozměry DPS')
    ptp_dps_rozmery_unit = fields.Many2one('ptp.delka.unit', string='Rozměr jednotka')
    ptp_dps_pocet_vrstev_value = fields.Integer(string='Počet vrstev')
    ptp_dps_pocet_vrstev_unit = fields.Char(string='ks')
    ptp_dps_tloustka_value = fields.Float(string='Tloušťka')
    ptp_dps_tloustka_unit = fields.Many2one('ptp.delka.unit', string='Tloušťka jednotka')
    ptp_dps_povrchova_uprava = fields.Many2one('ptp.dps.povrchova_uprava', string='Povrchová úprava')
    ptp_dps_material = fields.Many2one('ptp.dps.material', string='Materiál')
    # Jednotlivá pole SAB
    ptp_sab_typ = fields.Many2one('ptp.sab.typ', string='Typ šablony')
    ptp_sab_rozmer = fields.Text(string='Rozmer')
    ptp_sab_typ_uchyceni = fields.Many2one('ptp.sab.typ_uchyceni', string='Typ uchycení')
    # Jednotlivá pole NAP
    ptp_nap_typ_konektoru = fields.Many2one('ptp.nap.typ_konektoru', string='Typ konektoru')
    ptp_nap_pocet_pinu_value = fields.Integer(string='Počet pinů')
    ptp_nap_pocet_pinu_unit = fields.Char(string='pin')
    ptp_nap_montaz = fields.Many2one('ptp.nap.montaz', string='Montáž')
    ptp_nap_roztec_kontaktu_value = fields.Float(string='Rozteč kontaktů')
    ptp_nap_roztec_kontaktu_unit = fields.Many2one('ptp.delka.unit', string='Rozteč kontaktů jednotka')
    # Jednotlivá pole PIN
    ptp_pin_roztec_kontaktu_value = fields.Float(string='Rozteč kontaktů')
    ptp_pin_roztec_kontaktu_unit = fields.Many2one('ptp.delka.unit', string='Rozteč kontaktů jednotka')
    ptp_pin_typ = fields.Many2one('ptp.pin.typ', string='Typ Pinů')
    ptp_pin_pocet_pinu_value = fields.Integer(string='Počet pinů')
    ptp_pin_pocet_pinu_unit = fields.Char(string='pin')
    ptp_pin_montaz = fields.Many2one('ptp.pin.montaz', string='Montáž')
    # Jednotlivá pole USB
    ptp_usb_typ = fields.Many2one('ptp.usb.typ', string='Typ USB')
    # Jednotlivá pole ZAS
    ptp_zas_typ_konektoru = fields.Many2one('ptp.zas.typ_konektoru', string='Typ konektoru')
    ptp_zas_pocet_pinu_value = fields.Integer(string='Počet pinů')
    ptp_zas_pocet_pinu_unit = fields.Char(string='pin')
    ptp_zas_montaz = fields.Many2one('ptp.zas.montaz', string='Montáž')
    # Jednotlivá pole CHL
    ptp_chl_rozmery = fields.Char(string='Rozměry chladiče')
    ptp_chl_material = fields.Many2one('ptp.chl.material', string='Materiál')
    # Jednotlivá pole DRB
    ptp_drb_typ_baterie = fields.Many2one('ptp.drb.typ_baterie', string='Typ baterie')
    ptp_drb_pocet_clanku_value = fields.Integer(string='Počet článků')
    ptp_drb_pocet_clanku_unit = fields.Char(string='ks')
    ptp_drb_montaz = fields.Many2one('ptp.drb.montaz', string='Montáž')
    # Jednotlivá pole DRP
    ptp_drp_typ_pojistky = fields.Many2one('ptp.drp.typ_pojistky', string='Typ pojistky')
    ptp_drp_montaz = fields.Many2one('ptp.drp.montaz', string='Montáž')
    # Jednotlivá pole TLA
    ptp_tla_typ = fields.Many2one('ptp.tla.typ', string='Typ')
    ptp_tla_pocet_poloh_value = fields.Integer(string='Počet poloh')
    ptp_tla_pocet_poloh_unit = fields.Char(string='poloh')
    ptp_tla_montaz = fields.Many2one('ptp.tla.montaz', string='Montáž')
    # Jednotlivá pole BLU
    ptp_blu_typ = fields.Many2one('ptp.blu.typ', string='Typ bluetooth a wifi')
    # Jednotlivá pole DIS
    ptp_dis_typ = fields.Many2one('ptp.dis.typ', string='Typ Displeje')
    # Jednotlivá pole PLC
    ptp_plc_typ = fields.Many2one('ptp.plc.typ', string='Typ PLC')
    # Jednotlivá pole HDD
    ptp_hdd_typ = fields.Many2one('ptp.hdd.typ', string='Typ HDD')
    ptp_hdd_kapacita_value = fields.Float(string='Kapacita')
    ptp_hdd_kapacita_unit = fields.Many2one('ptp.hdd.kapacita_unit', string='Kapacita HDD Unit')
    # Jednotlivá pole SEN
    ptp_sen_merena_velicina = fields.Many2one('ptp.sen.merena_velicina', string='Měřená veličina senzoru')
    ptp_sen_typ_vystupu = fields.Many2one('ptp.usb.typ_vystupu', string='Typ výstupu senzoru')
    # Jednotlivá pole BAT
    ptp_bat_typ = fields.Many2one('ptp.bat.typ', string='Typ baterie')
    ptp_bat_napeti_value = fields.Float(string='Napětí baterie')
    ptp_bat_napeti_unit = fields.Many2one('ptp.napeti.unit', string='Unit (napětí)')
    ptp_bat_kapacita_value = fields.Float(string='Kapacita baterie')
    ptp_bat_kapacita_unit = fields.Many2one('ptp.bat.kapacita_unit', string='Kapacita baterie')
    ptp_bat_chemie = fields.Many2one('ptp.bat.chemie', string='Chemie')
    # Jednotlivá pole POJ
    ptp_poj_proud_value = fields.Float(string='Proud')
    ptp_poj_proud_unit = fields.Many2one('ptp.proud.unit', string='Unit (proud)')
    ptp_poj_napeti_value = fields.Float(string='Napětí')
    ptp_poj_napeti_unit = fields.Many2one('ptp.napeti.unit', string='Unit (napětí)')
    ptp_poj_typ = fields.Many2one('ptp.poj.typ', string='Rychlost pojistky')
    ptp_poj_typ_pojistky = fields.Many2one('ptp.poj.typ_pojistky', string='Typ pojistky')
    # Jednotlivá pole TVS
    ptp_tvs_napeti_value = fields.Float(string='Napětí')
    ptp_tvs_napeti_unit = fields.Many2one('ptp.napeti.unit', string='Unit (napětí)')
    ptp_tvs_proud_value = fields.Float(string='Proud')
    ptp_tvs_proud_unit = fields.Many2one('ptp.proud.unit', string='Unit (proud)')
    ptp_tvs_typ = fields.Many2one('ptp.tvs.typ', string='Typ TVS')
    ptp_tvs_polarity = fields.Many2one('ptp.tvs.polarity', string='TVS dioda polarity')
    ptp_tvs_chanel = fields.Many2one('ptp.tvs.chanel', string='TVS dioda počet kanálů')
    # Jednotlivá pole VAR
    ptp_var_napeti_value = fields.Float(string='Napětí')
    ptp_var_napeti_unit = fields.Many2one('ptp.napeti.unit', string='Unit (napětí)')
    ptp_var_proud_value = fields.Float(string='Proud')
    ptp_var_proud_unit = fields.Many2one('ptp.proud.unit', string='Unit (proud)')
    # Jednotlivá pole LED
    ptp_led_barva = fields.Many2one('ptp.led.barva', string='Barva')
    ptp_led_proud_value = fields.Float(string='Proud')
    ptp_led_proud_unit = fields.Many2one('ptp.proud.unit', string='Unit (proud)')
    ptp_led_napeti_value = fields.Float(string='Napětí')
    ptp_led_napeti_unit = fields.Many2one('ptp.napeti.unit', string='Unit (napětí)')
    # Jednotlivá pole LAD
    ptp_lad_vlnova_delka_value = fields.Float(string='Vlnová délka')
    ptp_lad_vlnova_delka_unit = fields.Char(string='nm')
    ptp_lad_proud_value = fields.Float(string='Proud')
    ptp_lad_proud_unit = fields.Many2one('ptp.proud.unit', string='Unit (proud)')
    ptp_lad_napeti_value = fields.Float(string='Napětí')
    ptp_lad_napeti_unit = fields.Many2one('ptp.napeti.unit', string='Unit (napětí)')
    # Jednotlivá pole DIO
    ptp_dio_typ = fields.Many2one('ptp.dio.typ', string='Typ')
    ptp_dio_napeti_value = fields.Float(string='Napětí')
    ptp_dio_napeti_unit = fields.Many2one('ptp.napeti.unit', string='Unit (napětí)')
    ptp_dio_proud_value = fields.Float(string='Proud')
    ptp_dio_proud_unit = fields.Many2one('ptp.proud.unit', string='Unit (proud)')
    # Jednotlivá pole SCH
    ptp_sch_ifpropustny_proud_value = fields.Float(string='If – propustný proud')
    ptp_sch_ifpropustny_proud_unit = fields.Many2one('ptp.proud.unit', string='Unit (proud)')
    ptp_sch_vrrm_value = fields.Float(string='Vrrm – opakované závěrné napětí')
    ptp_sch_vrrm_unit = fields.Many2one('ptp.napeti.unit', string='Unit (napětí)')
    # Jednotlivá pole USM
    ptp_usm_if_value = fields.Float(string='If – propustný proud')
    ptp_usm_if_unit = fields.Many2one('ptp.proud.unit', string='Unit (proud)')
    ptp_usm_vr_value = fields.Float(string='Vr – závěrné napětí')
    ptp_usm_vr_unit = fields.Many2one('ptp.napeti.unit', string='Unit (napětí)')
    # Jednotlivá pole ZEN
    ptp_zen_vz_value = fields.Float(string='Vz – Zenerovo napětí')
    ptp_zen_vz_unit = fields.Many2one('ptp.napeti.unit', string='Unit (napětí)')
    # Jednotlivá pole INT
    ptp_int_typ = fields.Many2one('ptp.int.typ', string='Typ Integrovaného obvodu')
    ptp_int_funkce = fields.Text(string='Funkce')
    # Jednotlivá pole TYR
    ptp_tyr_napeti_value = fields.Float(string='Napětí tyristoru')
    ptp_tyr_napeti_unit = fields.Many2one('ptp.napeti.unit', string='Unit (napětí)')
    ptp_tyr_proud_value = fields.Float(string='Proud tyristoru')
    ptp_tyr_proud_unit = fields.Many2one('ptp.proud.unit', string='Unit (proud)')
    # Jednotlivá pole BIP
    ptp_bip_typ = fields.Many2one('ptp.bip.typ', string='Typ Bipolárního tranzistoru')
    ptp_bip_napeti_uce_value = fields.Float(string='Napetí Uce')
    ptp_bip_napeti_uce_unit = fields.Many2one('ptp.napeti.unit', string='Unit (napětí)')
    ptp_bip_proud_ice_value = fields.Float(string='Proud Ice')
    ptp_bip_proud_ice_unit = fields.Many2one('ptp.proud.unit', string='Unit (proud)')
    # Jednotlivá pole UNI
    ptp_uni_typ_value = fields.Many2one('ptp.uni.typ', string='Typ Unipolárního tranzistoru')
    ptp_uni_napeti_vds_value = fields.Float(string='Napeti Vds')
    ptp_uni_napeti_vds_unit = fields.Many2one('ptp.napeti.unit', string='Unit (napětí)')
    ptp_uni_proud_ids_value = fields.Float(string='Proud Ids')
    ptp_uni_proud_ids_unit = fields.Many2one('ptp.proud.unit', string='Unit (proud)')
    # Jednotlivá pole MAS
    ptp_mas_sirka_value = fields.Float(string='Šířka')
    ptp_mas_sirka_unit = fields.Many2one('ptp.delka.unit', string='Šířka jednotka')
    ptp_mas_material = fields.Many2one('ptp.mas.material', string='Materiál')
    # Jednotlivá pole PAS
    ptp_pas_typ_value = fields.Many2one('ptp.pas.typ', string='Typ pasty')
    ptp_pas_slozeni = fields.Many2one('ptp.pas.slozeni', string='Složení')
    # Pole pro kondenzátory
    ptp_cap_value = fields.Char(string='Value (C)')
    ptp_cap_unit = fields.Many2one('ptp.cap.unit', string='Unit (C)')
    ptp_cap_voltage_rating = fields.Char(string='Voltage Rating [VDC]')
    ptp_cap_dielectric = fields.Many2one('ptp.cap.dielectric', string='Dielectric')
    ptp_cap_tolerance = fields.Char(string='Tolerance [%]')
    # Pole pro rezistory
    ptp_res_value = fields.Char(string='Value (R)')
    ptp_res_unit = fields.Many2one('ptp.res.unit', string='Unit (R)')
    ptp_res_power_rating = fields.Char(string='Power Rating')
    ptp_res_tolerance = fields.Char(string='Tolerance [%]')
    ptp_res_voltage_rating = fields.Char(string='Voltage Rating [V]')
    # Pole pro Feritové perličky
    ptp_imp_value = fields.Char(string="Impedance")
    ptp_imp_unit = fields.Many2one('ptp.imp.unit', string='Unit (Z)')
    # Pole pro Induktory
    ptp_ind_value = fields.Char(string="Induktance")
    ptp_ind_unit = fields.Many2one('ptp.ind.unit', string='Unit (X)')
    # Pole pro Tranzistory
    ptp_tra_polarity = fields.Many2one('ptp.tra.polarity', string='Tranzistor polarity')
    ptp_tra_type = fields.Many2one('ptp.tra.type', string='Tranzistor typ')
    
    ptp_bat_kapacita_full_value = fields.Char(string="Ptp Bat Kapacita Full Value", compute="_compute_all_full_values", store=True)
    ptp_bat_napeti_full_value = fields.Char(string="Ptp Bat Napeti Full Value", compute="_compute_all_full_values", store=True)
    ptp_bip_napeti_uce_full_value = fields.Char(string="Ptp Bip Napeti Uce Full Value", compute="_compute_all_full_values", store=True)
    ptp_bip_proud_ice_full_value = fields.Char(string="Ptp Bip Proud Ice Full Value", compute="_compute_all_full_values", store=True)
    ptp_cap_full_value = fields.Char(string="Ptp Cap Full Value", compute="_compute_all_full_values", store=True)
    ptp_dio_napeti_full_value = fields.Char(string="Ptp Dio Napeti Full Value", compute="_compute_all_full_values", store=True)
    ptp_dio_proud_full_value = fields.Char(string="Ptp Dio Proud Full Value", compute="_compute_all_full_values", store=True)
    ptp_dps_pocet_vrstev_full_value = fields.Char(string="Ptp Dps Pocet Vrstev Full Value", compute="_compute_all_full_values", store=True)
    ptp_dps_rozmery_full_value = fields.Char(string="Ptp Dps Rozmery Full Value", compute="_compute_all_full_values", store=True)
    ptp_dps_tloustka_full_value = fields.Char(string="Ptp Dps Tloustka Full Value", compute="_compute_all_full_values", store=True)
    ptp_drb_pocet_clanku_full_value = fields.Char(string="Ptp Drb Pocet Clanku Full Value", compute="_compute_all_full_values", store=True)
    ptp_imp_full_value = fields.Char(string="Ptp Imp Full Value", compute="_compute_all_full_values", store=True)
    ptp_ind_full_value = fields.Char(string="Ptp Ind Full Value", compute="_compute_all_full_values", store=True)
    ptp_lad_napeti_full_value = fields.Char(string="Ptp Lad Napeti Full Value", compute="_compute_all_full_values", store=True)
    ptp_lad_proud_full_value = fields.Char(string="Ptp Lad Proud Full Value", compute="_compute_all_full_values", store=True)
    ptp_lad_vlnova_delka_full_value = fields.Char(string="Ptp Lad Vlnova Delka Full Value", compute="_compute_all_full_values", store=True)
    ptp_led_napeti_full_value = fields.Char(string="Ptp Led Napeti Full Value", compute="_compute_all_full_values", store=True)
    ptp_led_proud_full_value = fields.Char(string="Ptp Led Proud Full Value", compute="_compute_all_full_values", store=True)
    ptp_mas_sirka_full_value = fields.Char(string="Ptp Mas Sirka Full Value", compute="_compute_all_full_values", store=True)
    ptp_nap_pocet_pinu_full_value = fields.Char(string="Ptp Nap Pocet Pinu Full Value", compute="_compute_all_full_values", store=True)
    ptp_nap_roztec_kontaktu_full_value = fields.Char(string="Ptp Nap Roztec Kontaktu Full Value", compute="_compute_all_full_values", store=True)
    ptp_pin_pocet_pinu_full_value = fields.Char(string="Ptp Pin Pocet Pinu Full Value", compute="_compute_all_full_values", store=True)
    ptp_pin_roztec_kontaktu_full_value = fields.Char(string="Ptp Pin Roztec Kontaktu Full Value", compute="_compute_all_full_values", store=True)
    ptp_poj_napeti_full_value = fields.Char(string="Ptp Poj Napeti Full Value", compute="_compute_all_full_values", store=True)
    ptp_poj_proud_full_value = fields.Char(string="Ptp Poj Proud Full Value", compute="_compute_all_full_values", store=True)
    ptp_res_full_value = fields.Char(string="Ptp Res Full Value", compute="_compute_all_full_values", store=True)
    ptp_sch_ifpropustny_proud_full_value = fields.Char(string="Ptp Sch Ifpropustny Proud Full Value", compute="_compute_all_full_values", store=True)
    ptp_sch_vrrm_full_value = fields.Char(string="Ptp Sch Vrrm Full Value", compute="_compute_all_full_values", store=True)
    ptp_tla_pocet_poloh_full_value = fields.Char(string="Ptp Tla Pocet Poloh Full Value", compute="_compute_all_full_values", store=True)
    ptp_tvs_napeti_full_value = fields.Char(string="Ptp Tvs Napeti Full Value", compute="_compute_all_full_values", store=True)
    ptp_tvs_proud_full_value = fields.Char(string="Ptp Tvs Proud Full Value", compute="_compute_all_full_values", store=True)
    ptp_tyr_napeti_full_value = fields.Char(string="Ptp Tyr Napeti Full Value", compute="_compute_all_full_values", store=True)
    ptp_tyr_proud_full_value = fields.Char(string="Ptp Tyr Proud Full Value", compute="_compute_all_full_values", store=True)
    ptp_uni_napeti_vds_full_value = fields.Char(string="Ptp Uni Napeti Vds Full Value", compute="_compute_all_full_values", store=True)
    ptp_uni_proud_ids_full_value = fields.Char(string="Ptp Uni Proud Ids Full Value", compute="_compute_all_full_values", store=True)
    ptp_usm_if_full_value = fields.Char(string="Ptp Usm If Full Value", compute="_compute_all_full_values", store=True)
    ptp_usm_vr_full_value = fields.Char(string="Ptp Usm Vr Full Value", compute="_compute_all_full_values", store=True)
    ptp_var_napeti_full_value = fields.Char(string="Ptp Var Napeti Full Value", compute="_compute_all_full_values", store=True)
    ptp_var_proud_full_value = fields.Char(string="Ptp Var Proud Full Value", compute="_compute_all_full_values", store=True)
    ptp_zas_pocet_pinu_full_value = fields.Char(string="Ptp Zas Pocet Pinu Full Value", compute="_compute_all_full_values", store=True)
    ptp_zen_vz_full_value = fields.Char(string="Ptp Zen Vz Full Value", compute="_compute_all_full_values", store=True)
    ptp_hdd_kapacita_full_value = fields.Char(string="HDD kap full value", compute="_compute_all_full_values", store=True)

    # ------------------------------------------
    # Sloučené hodnoty a kontroly
    # ------------------------------------------

    @api.depends(
        'ptp_bat_kapacita_value', 'ptp_bat_kapacita_unit',
        'ptp_bat_napeti_value', 'ptp_bat_napeti_unit',
        'ptp_bip_napeti_uce_value', 'ptp_bip_napeti_uce_unit',
        'ptp_bip_proud_ice_value', 'ptp_bip_proud_ice_unit',
        'ptp_cap_value', 'ptp_cap_unit',
        'ptp_dio_napeti_value', 'ptp_dio_napeti_unit',
        'ptp_dio_proud_value', 'ptp_dio_proud_unit',
        'ptp_dps_pocet_vrstev_value', 'ptp_dps_pocet_vrstev_unit',
        'ptp_dps_rozmery_value', 'ptp_dps_rozmery_unit',
        'ptp_dps_tloustka_value', 'ptp_dps_tloustka_unit',
        'ptp_drb_pocet_clanku_value', 'ptp_drb_pocet_clanku_unit',
        'ptp_imp_value', 'ptp_imp_unit',
        'ptp_ind_value', 'ptp_ind_unit',
        'ptp_lad_napeti_value', 'ptp_lad_napeti_unit',
        'ptp_lad_proud_value', 'ptp_lad_proud_unit',
        'ptp_lad_vlnova_delka_value', 'ptp_lad_vlnova_delka_unit',
        'ptp_led_napeti_value', 'ptp_led_napeti_unit',
        'ptp_led_proud_value', 'ptp_led_proud_unit',
        'ptp_mas_sirka_value', 'ptp_mas_sirka_unit',
        'ptp_nap_pocet_pinu_value', 'ptp_nap_pocet_pinu_unit',
        'ptp_nap_roztec_kontaktu_value', 'ptp_nap_roztec_kontaktu_unit',
        'ptp_pin_pocet_pinu_value', 'ptp_pin_pocet_pinu_unit',
        'ptp_pin_roztec_kontaktu_value', 'ptp_pin_roztec_kontaktu_unit',
        'ptp_poj_napeti_value', 'ptp_poj_napeti_unit',
        'ptp_poj_proud_value', 'ptp_poj_proud_unit',
        'ptp_res_value', 'ptp_res_unit',
        'ptp_sch_ifpropustny_proud_value', 'ptp_sch_ifpropustny_proud_unit',
        'ptp_sch_vrrm_value', 'ptp_sch_vrrm_unit',
        'ptp_tla_pocet_poloh_value', 'ptp_tla_pocet_poloh_unit',
        'ptp_tvs_napeti_value', 'ptp_tvs_napeti_unit',
        'ptp_tvs_proud_value', 'ptp_tvs_proud_unit',
        'ptp_tyr_napeti_value', 'ptp_tyr_napeti_unit',
        'ptp_tyr_proud_value', 'ptp_tyr_proud_unit',
        'ptp_uni_napeti_vds_value', 'ptp_uni_napeti_vds_unit',
        'ptp_uni_proud_ids_value', 'ptp_uni_proud_ids_unit',
        'ptp_usm_if_value', 'ptp_usm_if_unit',
        'ptp_usm_vr_value', 'ptp_usm_vr_unit',
        'ptp_var_napeti_value', 'ptp_var_napeti_unit',
        'ptp_var_proud_value', 'ptp_var_proud_unit',
        'ptp_zas_pocet_pinu_value', 'ptp_zas_pocet_pinu_unit',
        'ptp_zen_vz_value', 'ptp_zen_vz_unit',
        'ptp_hdd_kapacita_value', 'ptp_hdd_kapacita_unit'
    )
    def _compute_all_full_values(self):
        for rec in self:
            for attr in [
                'ptp_bat_kapacita','ptp_hdd_kapacita', 'ptp_bat_napeti', 'ptp_bip_napeti_uce', 'ptp_bip_proud_ice', 'ptp_cap',
                'ptp_dio_napeti', 'ptp_dio_proud', 'ptp_dps_pocet_vrstev', 'ptp_dps_rozmery', 'ptp_dps_tloustka',
                'ptp_drb_pocet_clanku', 'ptp_imp', 'ptp_ind', 'ptp_lad_napeti', 'ptp_lad_proud',
                'ptp_lad_vlnova_delka', 'ptp_led_napeti', 'ptp_led_proud', 'ptp_mas_sirka', 'ptp_nap_pocet_pinu',
                'ptp_nap_roztec_kontaktu', 'ptp_pin_pocet_pinu', 'ptp_pin_roztec_kontaktu', 'ptp_poj_napeti',
                'ptp_poj_proud', 'ptp_res', 'ptp_sch_ifpropustny_proud', 'ptp_sch_vrrm', 'ptp_tla_pocet_poloh',
                'ptp_tvs_napeti', 'ptp_tvs_proud', 'ptp_tyr_napeti', 'ptp_tyr_proud', 'ptp_uni_napeti_vds',
                'ptp_uni_proud_ids', 'ptp_usm_if', 'ptp_usm_vr', 'ptp_var_napeti', 'ptp_var_proud',
                'ptp_zas_pocet_pinu', 'ptp_zen_vz'
            ]:
                value = getattr(rec, f'{attr}_value', '') or ''
                unit_raw = getattr(rec, f'{attr}_unit', '')
                unit = unit_raw.name if hasattr(unit_raw, 'name') else unit_raw or ''
                setattr(rec, f'{attr}_full_value', f"{value}{unit}".strip())

    # ------------------------------------------
    # QR kody
    # ------------------------------------------
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

    # ------------------------------------------
    # Přenos description do SALE
    # ------------------------------------------

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

    
    # --------------------------------------------------------------------------------
    # Metoda pro vymazání starých dat, která nepatří k novému typu
    # --------------------------------------------------------------------------------
    def _clear_fields_for_type(self, new_type):
        """
        Vymaže všechna pole začínající na 'ptp_' kromě 'ptp_part_number'.
        """
        for rec in self:
            for field_name in rec._fields:
                if field_name.startswith('ptp_') and field_name != 'ptp_part_number':
                    try:
                        setattr(rec, field_name, False)
                    except Exception:
                        pass  # některá pole mohou být readonly nebo computed

    # --------------------------------------------------------------------------------
    # Onchange: při změně kategorie v detailu produktu 
    # (když uživatel vybere jinou category) => vymažeme nepotřebná data
    # --------------------------------------------------------------------------------
    @api.onchange('categ_id')
    def _onchange_categ_id_clear_fields(self):
        new_type = self.categ_id.ptp_component_type or False
        self._clear_fields_for_type(new_type)
        self.ptp_category_type_related = new_type
        
        
    def _compute_value_unit_combined(self):
        for rec in self:
            prefix = f'ptp_{rec.ptp_category_type_related}_'
            combined_values = []

            for field_name, field_obj in rec._fields.items():
                if field_name.startswith(prefix) and not field_name.endswith('_full_value'):
                    value = getattr(rec, field_name, False)

                    if isinstance(value, models.BaseModel):  # Many2one
                        value = value.name or ''
                    elif isinstance(value, (int, float)):
                        value = str(value)
                    elif not value:
                        continue

                    value = str(value).strip()
                    if value:
                        combined_values.append(value)

            rec.ptp_value_unit_combined = ' '.join(combined_values) if combined_values else False
    # --------------------------------------------------------------------------------
    # Validace: zkontroluje jen pole relevantní k finálnímu typu
    # --------------------------------------------------------------------------------
    @api.constrains('ptp_part_number')
    def _check_required_fields(self):
        for rec in self:
            ctype = rec.categ_id.ptp_component_type if rec.categ_id else None
            if not ctype or ctype == 'other':
                continue

            if not rec.ptp_part_number:
                raise ValidationError("Pole 'Part Number' je povinné.")

            prefix = f'ptp_{ctype}_'
            for field_name in rec._fields:
                if not field_name.startswith(prefix):
                    continue
                if field_name in ('ptp_note', 'ptp_value_unit_combined'):
                    continue
                field = rec._fields[field_name]
                value = getattr(rec, field_name)

                # Many2one: kontrola, že záznam je vyplněn
                if isinstance(field, fields.Many2one):
                    if not value:
                        raise ValidationError(f"Pole '{field.string}' je povinné.")
                # Float / Char / Integer
                elif isinstance(field, (fields.Float, fields.Char, fields.Integer)):
                    if value in (None, '', 0):
                        raise ValidationError(f"Pole '{field.string}' je povinné.")

    # --------------------------------------------------------------------------------
    # Generování interní reference
    # --------------------------------------------------------------------------------
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
        # Získání nového nebo existujícího part_number
        part_number = vals.get('ptp_part_number', self.ptp_part_number or "")

        # Oprava: zajistíme, že `part_number` je vždy řetězec
        if not isinstance(part_number, str):
            part_number = ""

        part_number = part_number.strip()
        existing_name = vals.get('name', self.name or "").strip()

        # Pokud máme novou kategorii a `ptp_part_number` je odstraněn, použijeme jeho hodnotu z `vals`
        if 'categ_id' in vals and not part_number and 'ptp_part_number' in vals:
            part_number = vals['ptp_part_number']

        # Pokud `ptp_part_number` není vyplněný, necháme původní název beze změny
        if not part_number:
            return existing_name

        # Rozdělíme existující název na části a odstraníme starý `ptp_part_number`
        name_parts = existing_name.split()
        old_part_number = self.ptp_part_number or ""
        name_parts = [part for part in name_parts if part != old_part_number]

        # Přidáme nový `ptp_part_number` na začátek názvu
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


class PtpBatChemie(models.Model):
    _name = 'ptp.bat.chemie'
    _description = 'Chemie baterie'
    name = fields.Char(string='Name', required=True)


class PtpBatKapacitaUnit(models.Model):
    _name = 'ptp.bat.kapacita_unit'
    _description = 'Kapacita baterie unit'
    name = fields.Char(string='Name', required=True)


class PtpBatTyp(models.Model):
    _name = 'ptp.bat.typ'
    _description = 'Typ baterie'
    name = fields.Char(string='Name', required=True)


class PtpBipTyp(models.Model):
    _name = 'ptp.bip.typ'
    _description = 'Typ bipolárního tranzistoru'
    name = fields.Char(string='Name', required=True)


class PtpBluTyp(models.Model):
    _name = 'ptp.blu.typ'
    _description = 'Typ bluetooth wifi'
    name = fields.Char(string='Name', required=True)


class PtpCapDielectric(models.Model):
    _name = 'ptp.cap.dielectric'
    _description = 'Dielectric'
    name = fields.Char(string='Name', required=True)


class PtpCapUnit(models.Model):
    _name = 'ptp.cap.unit'
    _description = 'Unit (C)'
    name = fields.Char(string='Name', required=True)


class PtpChlMaterial(models.Model):
    _name = 'ptp.chl.material'
    _description = 'Materiál chladiče'
    name = fields.Char(string='Name', required=True)


class PtpDelkaUnit(models.Model):
    _name = 'ptp.delka.unit'
    _description = 'Unit délky'
    name = fields.Char(string='Name', required=True)


class PtpDioTyp(models.Model):
    _name = 'ptp.dio.typ'
    _description = 'Typ diody'
    name = fields.Char(string='Name', required=True)


class PtpDisTyp(models.Model):
    _name = 'ptp.dis.typ'
    _description = 'Typ displeje'
    name = fields.Char(string='Name', required=True)


class PtpDpsMaterial(models.Model):
    _name = 'ptp.dps.material'
    _description = 'Material DPS'
    name = fields.Char(string='Name', required=True)


class PtpDpsPovrchovaUprava(models.Model):
    _name = 'ptp.dps.povrchova_uprava'
    _description = 'Povrchova uprava'
    name = fields.Char(string='Name', required=True)


class PtpDrbMontaz(models.Model):
    _name = 'ptp.drb.montaz'
    _description = 'Montaz držáku'
    name = fields.Char(string='Name', required=True)


class PtpDrbTypBaterie(models.Model):
    _name = 'ptp.drb.typ_baterie'
    _description = 'Typ držáku baterie'
    name = fields.Char(string='Name', required=True)


class PtpDrpMontaz(models.Model):
    _name = 'ptp.drp.montaz'
    _description = 'Montaz držáku pojistky'
    name = fields.Char(string='Name', required=True)


class PtpDrpTypPojistky(models.Model):
    _name = 'ptp.drp.typ_pojistky'
    _description = 'Typ držáku pojistky'
    name = fields.Char(string='Name', required=True)


class PtpFootprint(models.Model):
    _name = 'ptp.footprint'
    _description = 'Footprint'
    name = fields.Char(string='Name', required=True)


class PtpHddKapacitaUnit(models.Model):
    _name = 'ptp.hdd.kapacita_unit'
    _description = 'Kapacita HDD unit'
    name = fields.Char(string='Name', required=True)


class PtpHddTyp(models.Model):
    _name = 'ptp.hdd.typ'
    _description = 'Typ HDD'
    name = fields.Char(string='Name', required=True)


class PtpImpUnit(models.Model):
    _name = 'ptp.imp.unit'
    _description = 'Unit (Z)'
    name = fields.Char(string='Name', required=True)


class PtpIndUnit(models.Model):
    _name = 'ptp.ind.unit'
    _description = 'Unit (X)'
    name = fields.Char(string='Name', required=True)


class PtpIntTyp(models.Model):
    _name = 'ptp.int.typ'
    _description = 'Typ integrovaného obvodu'
    name = fields.Char(string='Name', required=True)


class PtpMasMaterial(models.Model):
    _name = 'ptp.mas.material'
    _description = 'Material pásky'
    name = fields.Char(string='Name', required=True)


class PtpNapMontaz(models.Model):
    _name = 'ptp.nap.montaz'
    _description = 'Montaz napájecích konektorů'
    name = fields.Char(string='Name', required=True)


class PtpNapTypKonektoru(models.Model):
    _name = 'ptp.nap.typ_konektoru'
    _description = 'Typ napájecího konektoru'
    name = fields.Char(string='Name', required=True)


class PtpNapetiUnit(models.Model):
    _name = 'ptp.napeti.unit'
    _description = 'Unit (V)'
    name = fields.Char(string='Name', required=True)


class PtpPasSlozeni(models.Model):
    _name = 'ptp.pas.slozeni'
    _description = 'Slozeni pasty'
    name = fields.Char(string='Name', required=True)


class PtpPasTyp(models.Model):
    _name = 'ptp.pas.typ'
    _description = 'Typ pasty'
    name = fields.Char(string='Name', required=True)


class PtpPinMontaz(models.Model):
    _name = 'ptp.pin.montaz'
    _description = 'Montaz pin'
    name = fields.Char(string='Name', required=True)


class PtpPinTyp(models.Model):
    _name = 'ptp.pin.typ'
    _description = 'Typ pin'
    name = fields.Char(string='Name', required=True)


class PtpPlcTyp(models.Model):
    _name = 'ptp.plc.typ'
    _description = 'Typ PLC'
    name = fields.Char(string='Name', required=True)


class PtpPojTyp(models.Model):
    _name = 'ptp.poj.typ'
    _description = 'Rychlost pojistky'
    name = fields.Char(string='Name', required=True)


class PtpPojTypPojistky(models.Model):
    _name = 'ptp.poj.typ_pojistky'
    _description = 'Typ pojistky'
    name = fields.Char(string='Name', required=True)


class PtpProudUnit(models.Model):
    _name = 'ptp.proud.unit'
    _description = 'Unit (I)'
    name = fields.Char(string='Name', required=True)


class PtpResUnit(models.Model):
    _name = 'ptp.res.unit'
    _description = 'Unit (R)'
    name = fields.Char(string='Name', required=True)


class PtpSabTyp(models.Model):
    _name = 'ptp.sab.typ'
    _description = 'Typ šablony'
    name = fields.Char(string='Name', required=True)


class PtpSabTypUchyceni(models.Model):
    _name = 'ptp.sab.typ_uchyceni'
    _description = 'Typ uchyceni šablony'
    name = fields.Char(string='Name', required=True)


class PtpSchVrrm(models.Model):
    _name = 'ptp.sch.vrrm'
    _description = 'Vrrm'
    name = fields.Char(string='Name', required=True)


class PtpSenMerenaVelicina(models.Model):
    _name = 'ptp.sen.merena_velicina'
    _description = 'Merena velicina senzoru'
    name = fields.Char(string='Name', required=True)


class PtpTlaMontaz(models.Model):
    _name = 'ptp.tla.montaz'
    _description = 'Montaz tlačítka'
    name = fields.Char(string='Name', required=True)


class PtpTlaTyp(models.Model):
    _name = 'ptp.tla.typ'
    _description = 'Typ tlačítka'
    name = fields.Char(string='Name', required=True)


class PtpTranPolarity(models.Model):
    _name = 'ptp.tran.polarity'
    _description = 'Polarita tranzistoru'
    name = fields.Char(string='Name', required=True)


class PtpTranType(models.Model):
    _name = 'ptp.tran.type'
    _description = 'Type tranzistoru'
    name = fields.Char(string='Name', required=True)


class PtpTvsChannel(models.Model):
    _name = 'ptp.tvs.chanel'
    _description = 'Chanel TVS'
    name = fields.Char(string='Name', required=True)


class PtpTvsPolarity(models.Model):
    _name = 'ptp.tvs.polarity'
    _description = 'Polarita TVS'
    name = fields.Char(string='Name', required=True)


class PtpTvsTyp(models.Model):
    _name = 'ptp.tvs.typ'
    _description = 'Typ TVS'
    name = fields.Char(string='Name', required=True)


class PtpUniTyp(models.Model):
    _name = 'ptp.uni.typ'
    _description = 'Typ unipolárního tranzistoru'
    name = fields.Char(string='Name', required=True)


class PtpUsbTyp(models.Model):
    _name = 'ptp.usb.typ'
    _description = 'Typ USB'
    name = fields.Char(string='Name', required=True)


class PtpUsbTypVystupu(models.Model):
    _name = 'ptp.usb.typ_vystupu'
    _description = 'Typ USB vystupu'
    name = fields.Char(string='Name', required=True)


class PtpZasMontaz(models.Model):
    _name = 'ptp.zas.montaz'
    _description = 'Montaz zásuvek'
    name = fields.Char(string='Name', required=True)


class PtpZasTypKonektoru(models.Model):
    _name = 'ptp.zas.typ_konektoru'
    _description = 'Typ zásuvky konektoru'
    name = fields.Char(string='Name', required=True)


class PtpLedBarva(models.Model):
    _name = 'ptp.led.barva'
    _description = 'Barva LED'
    name = fields.Char(string='Name', required=True)
