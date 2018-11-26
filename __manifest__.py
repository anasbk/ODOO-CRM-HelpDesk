# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'CRM HelpDesk',
    'version': '10.0',
    'category': 'CRM',
    'license': 'AGPL-3',
    'author': "Odoo",
    'website': 'http://www.odoo.com/',
    'depends': ['base', 'crm', 'sale', 'sales_team', 'product'
                ],
    'images': ['images/main_screenshot.png'],
    'data': [
             'data/ir_sequence_data.xml',
             'views/res_partner_view.xml',
             'views/crm_helpdesk_view.xml',
             'views/crm_helpdesk_menu.xml',
             'views/product_view.xml',
             ],
    'installable': True,
    'application': True,
}
