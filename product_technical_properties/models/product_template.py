from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    ptp_cap_unit = fields.Many2one('ptp.unit', string='Capacitor Unit')
    ptp_res_unit = fields.Many2one('ptp.unit', string='Resistor Unit')
    
    @api.depends('ptp_cap_value', 'ptp_cap_unit', 'ptp_res_value', 'ptp_res_unit')
    def _compute_full_values(self):
        for record in self:
            record.ptp_res_full_value = f"{record.ptp_res_value} {record.ptp_res_unit.name}" if record.ptp_res_value and record.ptp_res_unit else ''
