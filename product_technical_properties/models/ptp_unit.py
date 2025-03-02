from odoo import models, fields

class PtpUnit(models.Model):
    _name = 'ptp.unit'
    _description = 'Technical Unit'
    
    name = fields.Char(string='Unit Name', required=True, translate=True)
