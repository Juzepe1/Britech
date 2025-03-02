# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    # Hodnoty kondenzátoru
    ptp_cap_part_number = fields.Char(string="Capacitor Part Number", required=True)
    ptp_cap_value = fields.Float(string="Capacitor Value", required=True)
    ptp_cap_unit = fields.Selection([
        ('pF', 'pF'), ('nF', 'nF'), ('uF', 'uF')], string="Capacitor Unit", required=True)
    ptp_cap_full_value = fields.Char(string="Capacitor Full Value", compute="_compute_full_values", store=True)
    ptp_cap_voltage_rating = fields.Float(string="Capacitor Voltage Rating [VDC]", required=True)
    ptp_cap_dielectric = fields.Selection([
        ('C0G_NP0', 'C0G (NP0)'), ('X5R', 'X5R'), ('X7R', 'X7R'),
        ('X6S', 'X6S'), ('X7S', 'X7S'), ('X7T', 'X7T')], string="Capacitor Dielectric", required=True)
    ptp_cap_tolerance = fields.Float(string="Capacitor Tolerance [%]")
    ptp_cap_footprint = fields.Selection([
        ('0201', '0201'), ('0402', '0402'), ('0603', '0603'), ('0805', '0805'),
        ('1206', '1206'), ('1210', '1210'), ('1216', '1216'), ('2010', '2010'),
        ('1812', '1812'), ('2220', '2220')], string="Capacitor Footprint", required=True)
    ptp_cap_note = fields.Text(string="Capacitor Note")

    # Hodnoty rezistoru
    ptp_res_part_number = fields.Char(string="Resistor Part Number", required=True)
    ptp_res_value = fields.Float(string="Resistor Value", required=True)
    ptp_res_unit = fields.Selection([
        ('mOhm', 'mOhm'), ('Ohm', 'Ohm'), ('kOhm', 'kOhm'), ('MOhm', 'MOhm')], string="Resistor Unit", required=True)
    ptp_res_full_value = fields.Char(string="Resistor Full Value", compute="_compute_full_values", store=True)
    ptp_res_power_rating = fields.Char(string="Resistor Power Rating", required=True)
    ptp_res_tolerance = fields.Float(string="Resistor Tolerance [%]", required=True)
    ptp_res_voltage_rating = fields.Float(string="Resistor Voltage Rating [V]", required=True)
    ptp_res_footprint = fields.Selection([
        ('0201', '0201'), ('0402', '0402'), ('0603', '0603'), ('0805', '0805'),
        ('1206', '1206'), ('1210', '1210'), ('1216', '1216'), ('2010', '2010'),
        ('1812', '1812'), ('2220', '2220')], string="Resistor Footprint", required=True)
    ptp_res_note = fields.Text(string="Resistor Note")

    # Hodnoty dalších komponent
    ptp_other_part_number = fields.Char(string="Other Component Part Number", required=True)
    ptp_other_note = fields.Text(string="Other Component Note")

    @api.depends('ptp_cap_value', 'ptp_cap_unit', 'ptp_res_value', 'ptp_res_unit')
    def _compute_full_values(self):
        for record in self:
            record.ptp_cap_full_value = f"{record.ptp_cap_value} {record.ptp_cap_unit}" if record.ptp_cap_value and record.ptp_cap_unit else ''
            record.ptp_res_full_value = f"{record.ptp_res_value} {record.ptp_res_unit}" if record.ptp_res_value and record.ptp_res_unit else ''
