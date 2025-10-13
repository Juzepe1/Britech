
# -*- coding: utf-8 -*-
{
    "name": "BOM Import Assistant",
    "version": "18.0.6.0.0",
    "summary": "Step-by-step assistant to import and reconcile BOMs from files.",
    'author': 'Ing. Josef Dostál',
    'license': 'Other proprietary',
    "depends": ["mrp", "product", "base"],
    "data": [
        "security/ir.model.access.csv",
        "data/bom_import_sequence.xml",
    	"views/bom_line_ext_views.xml",
        "views/bom_import_views.xml"
    ],
    "installable": True,
    "application": False
}
