# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.tools.translate import _
from openerp.tools import html2plaintext


class CrmHelpdesk(models.Model):
    """ Helpdesk Cases """

    _name = "crm.helpdesk"
    _description = "Helpdesk"
    _order = "id desc" # ?
    _inherit = ['mail.thread'] # ?

    id = fields.Integer(string='ID', readonly=True)
    name = fields.Char(string='Name', required=True, readonly=True, default=lambda self: _('Nouveau')) #?
    store_id = fields.Many2one('res.partner', string='Magasin')
    seller_id = fields.Many2one('res.partner', string='Vendeur')
    supplier_id = fields.Many2one('res.partner', string='Fournisseur')
    lgs = fields.Boolean('LGS', related='supplier_id.lgs', store=True)
    carrier_reception = fields.Many2one('res.partner', string=u'Transporteur Réception')
    carrier_delivery = fields.Many2one('res.partner', string=u'Transporteur Livraison')
    type = fields.Many2one('sav.type', string='Type S.A.V')
    nature = fields.Many2one('sav.nature', string='Nature de la demande')
    motif = fields.One2many('sav.motif', 'helpdesk_id', string='Motifs')
    article_id = fields.Many2one('product.product', string='Article')
    qty = fields.Integer(string='Qty')
    piece = fields.Text(u'Piece')
    observation = fields.Text(u'Observation')
    additional_info = fields.Text(u'Information complementaire')
    email_from = fields.Char(string='Email', size=128, help="Destination email for email gateway")
    address = fields.Char(string='Adresse', size=128, help="Adresse du client")
    phone = fields.Char(string=u'Téléphone.', size=128, help=u"Téléphone du client")
    mobile = fields.Char(string=u'Mobile.', size=128, help=u"Mobile du client")
    active = fields.Boolean(string='Active', required=False, default=True)
    date_action_last = fields.Datetime(string='Last Action', readonly=1)
    date_action_next = fields.Datetime(string='Next Action', readonly=1)
    create_date = fields.Datetime(string='Creation Date', readonly=True)
    write_date = fields.Datetime(string='Update Date', readonly=True)
    reception_date = fields.Datetime(string='Date Reception')
    planned_date = fields.Datetime(string='Date planification')
    delivery_date = fields.Datetime(string='Date Livraison')
    date_deadline = fields.Date(string='Deadline')
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    priority = fields.Selection([('0', 'Low'), ('1', 'Normal'), ('2', 'High')], 'Priority', default='1')

    section_id = fields.Many2one('crm.team', 'Sales Team', \
                    select=True, help='Responsible sales team. Define Responsible user and Email account for mail gateway.')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('crm.helpdesk'))
    date_closed = fields.Datetime(string='Closed', readonly=True, copy=False)
    partner_id = fields.Many2one('res.partner', 'Client')
    email_cc = fields.Text('Watchers Emails', size=252 , help="These email addresses will be added to the CC field of all inbound and outbound emails for this record before being sent. Separate multiple email addresses with a comma")
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    planned_cost = fields.Float('Planned Costs')
    duration = fields.Float(string='Duration', states={'done': [('readonly', True)]})
    state = fields.Selection(
        [('draft', 'New'),
         ('waiting', 'Waiting'),
         ('open', 'In Progress'),
         ('pending', 'Pending'),
         ('done', 'Closed'),
         ('cancel', 'Cancelled')], string='Status', default='draft', track_visibility='onchange',
                          help='The status is set to \'Draft\', when a case is created.\
                          \nIf the case is in progress the status is set to \'Open\'.\
                          \nWhen the case is over, the status is set to \'Done\'.\
                          \nIf the case needs to be reviewed then the status is set to \'Pending\'.')

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nouveau') == 'Nouveau':
            vals['name'] = self.env['ir.sequence'].next_by_code('crm.helpdesk') or 'Nouveau'

        result = super(CrmHelpdesk, self).create(vals)
        return result


    # on change partner id, change
    @api.onchange('partner_id')
    def on_change_partner_id(self):
        values = {}
        for record in self:
            if record.partner_id:
                partner = self.env['res.partner'].browse(record.partner_id.id)
                values = {
                    'email_from': partner.email,
                    'address': partner.contact_address,
                    'phone': partner.phone,
                    'mobile': partner.mobile,
                }
        return {'value': values}
    # on change article id, change supplier id
    @api.onchange('article_id')
    def on_change_supplier_id(self):
        for record in self:
            if record.article_id:
                record.supplier_id = record.article_id.supplier_id
            else:
                record.supplier_id = False

    @api.onchange('lgs')
    def on_change_state(self):
        for record in self:
            if record.lgs:
                record.state = 'waiting'
            else:
                record.state = 'draft'

    @api.multi
    def action_approval(self):
        self.write({'state': 'open'})




    @api.multi
    def write(self, values):
        """ Override to add case management: open/close dates """
        if values.get('state'):
            if values.get('state') in ['draft', 'open'] and not values.get('date_open'):
                values['date_open'] = fields.datetime.now()
            elif values.get('state') == 'done' and not values.get('date_closed'):
                values['date_closed'] = fields.datetime.now()
        return super(CrmHelpdesk, self).write(values)


    # @api.multi
    # def case_escalate(self):
    #     """ Escalates case to parent level """
    #     data = {'active': True}
    #     for case in self.browse(self.ids):
    #         if case.section_id and case.section_id.parent_id:
    #             parent_id = case.section_id.parent_id
    #             data['section_id'] = parent_id.id
    #             if parent_id.change_responsible and parent_id.user_id:
    #                 data['user_id'] = parent_id.user_id.id
    #         else:
    #             raise UserError(_('Error!, You can not escalate, you are already at the top level regarding your sales-team category.'))
    #         case.write(data)
    #     return True

    # -------------------------------------------------------
    # Mail gateway
    # -------------------------------------------------------


    @api.multi
    def message_new(self, msg, custom_values=None):
        """ Overrides mail_thread message_new that is called by the mailgateway
            through message_process.
            This override updates the document according to the email.
        """
        if custom_values is None:
            custom_values = {}
        desc = html2plaintext(msg.get('body')) if msg.get('body') else ''
        defaults = {
            'name': msg.get('subject') or _("No Subject"),
            'description': desc,
            'email_from': msg.get('from'),
            'email_cc': msg.get('cc'),
            'user_id': False,
            'partner_id': msg.get('author_id', False),
        }
        defaults.update(custom_values)
        return super(CrmHelpdesk, self).message_new(msg, custom_values=defaults)

class SavType(models.Model):
    """ Helpdesk Type """

    _name = "sav.type"
    _description = "SAV Type"

    name = fields.Char(string='Name', required=True)


class SavNature(models.Model):
    """ Helpdesk Nature """

    _name = "sav.nature"
    _description = "SAV Nature"

    name = fields.Char(string='Name', required=True)

class SavMotif(models.Model):
    """ Helpdesk Motif """

    _name = "sav.motif"
    _description = "SAV Motif"

    helpdesk_id = fields.Many2one('crm.helpdesk', 'SAV')
    reason_id = fields.Many2one('sav.reason', 'Motif')
    sub_reason_ids = fields.Many2many('sav.sub.reason', string='Sous Motifs')

class SavReason(models.Model):
    """ Helpdesk Reason """

    _name = "sav.reason"
    _description = "SAV Reason"

    name = fields.Char(string='Nom', required=True)
    sub_reason_ids = fields.One2many('sav.sub.reason', 'reason_id', string='Sous Motifs')

class SavSubReason(models.Model):
    """ Helpdesk Sub reason """

    _name = "sav.sub.reason"
    _description = "SAV Sub Reason"

    name = fields.Char(string='Nom', required=True)
    reason_id = fields.Many2one('sav.reason', 'Motif')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
