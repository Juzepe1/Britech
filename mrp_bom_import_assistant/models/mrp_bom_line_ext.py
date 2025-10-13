# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    ptp_designator = fields.Char(string='Designator')

    ptp_tech_params = fields.Char(
        string='Description technical',
        compute='_compute_ptp_tech_params',
        store=True,
        readonly=True,
        help='Combined technical parameters pulled from the related product template if available.'
    )
    ptp_time_total = fields.Float(
        string='Total Time',
        compute='_compute_ptp_time_total',
        help='Quantity × (product time + footprint time). Non-stored for robustness.'
    )
    # dostupnost / forecast (jen ke čtení)
    ptp_qty_onhand = fields.Float(
        string='On Hand',
        compute='_compute_ptp_availability',
        digits='Product Unit of Measure',
        help='Current on-hand quantity of the BOM line product.'
    )
    ptp_qty_forecast = fields.Float(
        string='Forecasted',
        compute='_compute_ptp_availability',
        digits='Product Unit of Measure',
        help='Forecasted quantity (virtual available) of the BOM line product.'
    )

    @api.depends('product_tmpl_id', 'product_tmpl_id.write_date', 'product_id')
    def _compute_ptp_tech_params(self):
        tmpl_model = self.env['product.template']
        has_value_unit = 'ptp_value_unit_combined' in tmpl_model._fields
        has_unit_value = 'ptp_unit_value_combined' in tmpl_model._fields

        for line in self:
            val = False
            tmpl = line.product_tmpl_id
            if tmpl:
                if has_value_unit:
                    val = getattr(tmpl, 'ptp_value_unit_combined', False)
                if not val and has_unit_value:
                    val = getattr(tmpl, 'ptp_unit_value_combined', False)
            line.ptp_tech_params = val or False


    @api.depends('product_qty', 'product_id', 'product_id.write_date')
    def _compute_ptp_time_total(self):
        """Compute without hard depends on optional fields.
        Looks for candidate time fields dynamically:
          - on product template: 'time', then 'ptp_time'
          - on template's footprint (Many2one): 'time', 'ptp_time', 'duration', 'footprint_time'
        If field(s) not present, use 0.
        """
        for line in self:
            qty = float(line.product_qty or 0.0)
            tmpl = line.product_id.product_tmpl_id if line.product_id else line.product_tmpl_id

            # product time on template (optional)
            product_time = 0.0
            if tmpl:
                if 'time' in tmpl._fields:
                    product_time = float(getattr(tmpl, 'time') or 0.0)
                elif 'ptp_time' in tmpl._fields:
                    product_time = float(getattr(tmpl, 'ptp_time') or 0.0)

            # footprint time via Many2one (optional)
            footprint_time = 0.0
            if tmpl and 'ptp_footprint' in tmpl._fields and getattr(tmpl, 'ptp_footprint'):
                fp = tmpl.ptp_footprint.sudo()
                for cand in ('time', 'ptp_time', 'duration', 'footprint_time'):
                    if cand in fp._fields:
                        footprint_time = float(getattr(fp, cand) or 0.0)
                        break

            line.ptp_time_total = qty * (product_time + footprint_time)

    @api.depends('product_id', 'product_id.qty_available', 'product_id.virtual_available')
    def _compute_ptp_availability(self):
        for line in self:
            product = line.product_id or line.product_tmpl_id.product_variant_id
            if product:
                # respektuj společnost z řádku BOM (pokud je)
                with product.env.cr.savepoint():
                    p = product.with_company(line.company_id.id) if line.company_id else product
                line.ptp_qty_onhand = p.qty_available or 0.0
                line.ptp_qty_forecast = p.virtual_available or 0.0
            else:
                line.ptp_qty_onhand = 0.0
                line.ptp_qty_forecast = 0.0