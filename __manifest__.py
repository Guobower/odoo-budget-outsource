# -*- coding: utf-8 -*-
{
    'name': "Outsource",
    'version': '11.0.0.1',
    'summary': 'Outsource Management',
    'sequence': 9,
    'description': """
Odoo Module
===========
Specifically Designed for Etisalat-TBPC

Outsource Management
---------------------
- Approval
- Claim
- Resource
- Unit Rate
    """,
    'author': "Marc Philippe de Villeres",
    'website': "https://github.com/mpdevilleres",
    'category': 'TBPC Budget',
    'depends': ['base',
                'budget_enduser', 'budget_contractor', 'budget_capex', 'budget_opex', 'budget_purchase_order',
                'budget_invoice'],
    'data': [
        'security/budget_outsource.xml',
        'security/ir.model.access.csv',

        'views/mobilize.xml',
        'views/position.xml',
        'views/resource.xml',
        'views/unit_rate.xml',
        'views/datasheet.xml',
        'views/sbh.xml',

        'views/cear_inherit.xml',
        'views/contract_inherit.xml',
        'views/contractor_inherit.xml',
        'views/invoice_inherit.xml',
        'views/invoice_summary_inherit.xml',
        'views/oear_inherit.xml',
        'views/purchase_order_inherit.xml',

        'views/invoice_menu_inherit.xml',
        'views/menu.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
