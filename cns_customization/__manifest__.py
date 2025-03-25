###################################################################################
#
#    Copyright 2024 Systee s.r.o. (<https://www.systee.cz>)
#
#    Systee Enterprise License v1.0
#
#    This software and associated files (the "Software") may only be used
#    if you have purchased a valid license from Systee s.r.o.
#
#    The above permissions are granted for a single database per purchased
#    license. Furthermore, with a valid license it is permitted to use the
#    software on other databases as long as the usage is limited to a testing
#    or development environment.
#
#    You may develop modules based on the Software or that use the Software
#    as a library (typically by depending on it, importing it and using
#    its resources), but without copying any source code or material from
#    the Software.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies of
#    the Software or modified copies of the Software.
#
#    The Software may not be modified in any way, reverse-engineered,
#    or taken similar or other steps in order to use the source code.
#
###################################################################################

{
    'post_init_hook': 'post_init_hook',
    'name': 'CNS Customizations',
    'version': '17.0.0.0.4',
    'summary': "Customizations for CNS",
    'author': 'Josef Dostál',
    'maintainer': 'Systee s.r.o. (https://www.systee.cz)',
    'license': 'Other proprietary',
    'application': False,
    'installable': True,
    'category': 'Sales',
    'countries': [],
    'depends': [
        'base',
        'contacts'
    ],
    'data': [
        'data/sequence.xml',
        'views/res_partner_form_view.xml',
        'views/res_partner_export_action.xml'
    ],
    'assets': {
    },
    'description': """""",
}
