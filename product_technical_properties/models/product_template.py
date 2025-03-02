# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Hodnoty kondenzátoru
    ptp_cap_part_number = fields.Char(string="Capacitor Part Number", required=True)
    ptp_cap_value = fields.Float(string="Capacitor Value", required=True)
    ptp_cap_unit = fields.Char(string="Capacitor Unit", required=True)
    ptp_cap_voltage_rating = fields.Float(string="Capacitor Voltage Rating [VDC]", required=True)
    ptp_cap_dielectric = fields.Char(string="Capacitor Dielectric", required=True)
    ptp_cap_tolerance = fields.Float(string="Capacitor Tolerance [%]")
    ptp_cap_footprint = fields.Char(string="Capacitor Footprint", required=True)
    ptp_cap_note = fields.Text(string="Capacitor Note")

    # Hodnoty rezistoru
    ptp_res_part_number = fields.Char(string="Resistor Part Number", required=True)
    ptp_res_value = fields.Float(string="Resistor Value", required=True)
    ptp_res_unit = fields.Char(string="Resistor Unit", required=True)
    ptp_res_power_rating = fields.Char(string="Resistor Power Rating", required=True)
    ptp_res_tolerance = fields.Float(string="Resistor Tolerance [%]", required=True)
    ptp_res_voltage_rating = fields.Float(string="Resistor Voltage Rating [V]", required=True)
    ptp_res_footprint = fields.Char(string="Resistor Footprint", required=True)
    ptp_res_note = fields.Text(string="Resistor Note")

    # Hodnoty dalších komponent
    ptp_other_part_number = fields.Char(string="Other Component Part Number", required=True)
    ptp_other_note = fields.Text(string="Other Component Note")
