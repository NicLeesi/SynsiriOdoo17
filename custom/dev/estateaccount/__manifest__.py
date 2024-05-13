# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Estate Account',
    'version' : '1.0.0',
    'summary': 'Invoices for estate app',
    'sequence': 10,
    'description': """
Invoicing & Payments
====================
The specific and easy-to-use Invoicing system in Odoo allows you to keep track of your accounting, even when you are not an accountant. It provides an easy way to follow up on your vendors and customers.

You could use this simplified accounting in case you work with an (external) account to keep your books, and you still want to keep track of payments. This module also offers you an easy method of registering payments, without having to encode complete abstracts of account.
    """,
    'depends':['estate','account'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/estate_account_menuitem.xml'
    ],

    'installable': True,
    'application': True,

    'license': 'LGPL-3',
}
