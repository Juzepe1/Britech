from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pp_part_number = fields.Char(string='PP Part Number', required=True, default='N/A')
    pp_value = fields.Float(string='PP Value', required=True)
    pp_unit = fields.Selection([
        ('pF', 'pF'), ('nF', 'nF'), ('μF', 'μF'), ('mΩ', 'mΩ'), ('Ω', 'Ω'), ('kΩ', 'kΩ'), ('MΩ', 'MΩ')
    ], string='PP Unit')
    pp_voltage_rating_vdc = fields.Float(string='PP Voltage Rating [VDC]')
    pp_dielectric = fields.Selection([
        ('C0G', 'C0G (NP0)'), ('X5R', 'X5R'), ('X7R', 'X7R'), ('X6S', 'X6S'), ('X7S', 'X7S'), ('X7T', 'X7T')
    ], string='PP Dielectric')
    pp_tolerance = fields.Float(string='PP Tolerance [%]')
    pp_footprint = fields.Selection([
        ('0201', '0201'), ('0402', '0402'), ('0603', '0603'), ('0805', '0805'),
        ('1206', '1206'), ('1210', '1210'), ('1216', '1216'), ('2010', '2010'), ('1812', '1812'), ('2220', '2220')
    ], string='PP Footprint', required=True, default='0402')
    pp_note = fields.Text(string='PP Note')