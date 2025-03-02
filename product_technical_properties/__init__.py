# -*- coding: utf-8 -*-

from odoo import api, SUPERUSER_ID

def pre_init_hook(cr):
    """Kompletně odstraní konfliktní výběrové hodnoty v ir.model.fields a ir.model.fields.selection."""
    cr.execute("""
        DELETE FROM ir_model_fields_selection
        WHERE field_id IN (
            SELECT id FROM ir_model_fields 
            WHERE model IN ('product.template', 'product.category')
        );
    """)
    
    cr.execute("""
        DELETE FROM ir_model_fields 
        WHERE model IN ('product.template', 'product.category')
        AND name IN (
            'ptp_cap_unit', 'ptp_cap_dielectric', 'ptp_cap_footprint', 
            'ptp_res_unit', 'ptp_res_footprint', 'ptp_component_type'
        );
    """)

from . import models
