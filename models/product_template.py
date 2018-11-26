# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# clears
# no name in producttemplate!
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = "product.template"
    _description = "Product Template"

    lgs = fields.Boolean(string='LGS', default=False)
    supplier_id = fields.Many2one('res.partner', string='Fournisseur')
    crm_helpdesk_count = fields.Integer(compute='_compute_crm_helpdesk_count', string='Reclamations')

    @api.onchange('supplier_id')
    def onchange_lgs(self):
        self.lgs = self.supplier_id.lgs

    def _compute_crm_helpdesk_count(self):
        for product in self:
            product.crm_helpdesk_count = self.env['crm.helpdesk'].search_count([('article_id', 'in', self.ids)])
