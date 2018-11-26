# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# res partner has no name
# what is lgs
# read_group
# self.ids ?
#
#
#
#
#
#
#

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import facebook
import xmlrpclib

def getUserFromDb(fullname, models, common, db, uid, password):
    # Search for user with firstname and lastname

    users = models.execute_kw(db, uid, password,
                              'res.partner', 'search_read',
                              [[['name', 'ilike', fullname]]],
                              {'fields': ['name'], 'limit': 5})

    return users


def updateUserLike(users_list, like, post, models, common, db, uid, password):
    # Check if like already exists
    print('updateUserLike')

    for user in users_list:
        count = models.execute_kw(db, uid, password,
                                  'customer.facebook.like', 'search_count',
                                  [[['post_url', 'ilike', post['permalink_url']], ['liker_id', 'ilike', like['id']]]])

        print post['permalink_url']
        if count == 0:
            id = models.execute_kw(db, uid, password, 'customer.facebook.like', 'create', [{
                'post_url': post['permalink_url'], 'liker_id': like['id'], 'customer_id': user['id'],
                'like_type': like['type']
            }])


def updateUserComment(users_list, comment, post, models, common, db, uid, password):
    # Check if comment already exists

    print('updateUserComment')
    for user in users_list:
        count = models.execute_kw(db, uid, password,
                                  'customer.facebook.comment', 'search_count',
                                  [[['post_url', 'ilike', post['permalink_url']], ['comment_id', '=', comment['id']]]])

        # check if like already exists
        if count == 0:
            id = models.execute_kw(db, uid, password, 'customer.facebook.comment', 'create', [{
                'post_url': post['permalink_url'], 'comment_url': comment['permalink_url'], 'comment_id': comment['id'],
                'liker_id': comment['from']['id'], 'customer_id': user['id'], 'message_str': comment['message']
            }])

class ResPartner(models.Model):

    _inherit = "res.partner"
    _description = "Res Partner"

    seller = fields.Boolean(string='Vendeur', default=False) # is seller ?
    carrier = fields.Boolean(string='Transporteur', default=False) # is carrier ?
    store = fields.Boolean(string='Magasins', default=False) # is store ?
    store_id = fields.Many2one('res.partner', string='Magasin') # the store id
    lgs = fields.Boolean(string='LGS') #
    card_nbr = fields.Char(string='N de Carte') # card number
    sav_phone = fields.Char(string=u'Tel. SAV') # sav phone
    sav_resp = fields.Char(string=u'Resp. SAV') # sav resp ?
    birth_date = fields.Date(string='Date de naissance') # birthday why ?

    like = fields.One2many('customer.facebook.like','customer_id')
    comment = fields.One2many('customer.facebook.comment', 'customer_id')


    crm_helpdesk_count = fields.Integer(compute='_compute_crm_helpdesk_count', string='Reclamations')
    crm_likes_count = fields.Integer(compute='_compute_crm_likes_count', string='likes')
    crm_dislikes_count = fields.Integer(compute='_compute_crm_helpdesk_count', string='dislikes')
    crm_comments_count = fields.Integer(compute='_compute_crm_comments_count', string='comments')

    def _compute_crm_helpdesk_count(self):
        helpdesk_data = self.env['crm.helpdesk'].read_group(domain=[('partner_id', 'child_of', self.ids)],
                                                      fields=['partner_id'], groupby=['partner_id'])
        # read to keep the child/parent relation while aggregating the read_group result in the loop
        partner_child_ids = self.read(['child_ids'])
        mapped_data = dict([(m['partner_id'][0], m['partner_id_count']) for m in helpdesk_data])
        for partner in self:
            # let's obtain the partner id and all its child ids from the read up there
            partner_ids = filter(lambda r: r['id'] == partner.id, partner_child_ids)[0]
            partner_ids = [partner_ids.get('id')] + partner_ids.get('child_ids')
            # then we can sum for all the partner's child
            partner.crm_helpdesk_count = sum(mapped_data.get(child, 0) for child in partner_ids)

    def _compute_crm_dislikes_count(self):
        for customer in self:
            customer.crm_dislikes_count = self.env['customer.facebook.like'].search_count([('customer_id', 'in', self.ids), ('like_type', 'in', ['ANGRY', 'SAD'])])

    def _compute_crm_comments_count(self):
        for customer in self:
            customer.crm_comments_count = self.env['customer.facebook.comment'].search_count([('customer_id', 'in', self.ids)])

    def _compute_crm_likes_count(self):
        for customer in self:
            customer.crm_likes_count = self.env['customer.facebook.like'].search_count([('customer_id', 'in', self.ids),('like_type', 'in',['LIKE','LOVE','WOW','HAHA'])])



    def getPosts(self, posts_limit, graph):

        # Get posts of my page ( last posts_limit )
        posts = graph.get_connections(id='me', connection_name='posts', limit=posts_limit, fields="permalink_url")

        # loop to get list of comments and likes
        for post in posts['data']:
            print post['id']

            # List of likes
            reactions = graph.get_connections(id=post['id'], connection_name='reactions', limit=500, )

            for reaction in reactions['data']:
                print reaction['id']
                print reaction['type']

            # List of comments
            comments = graph.get_connections(id=post['id'], connection_name='comments', limit=500,
                                             fields='permalink_url,message,id,from')

            for comment in comments['data']:
                print comment['id']
                if 'from' in comment:
                    if 'name' in comment:
                        print comment['from']['name']

            post['reactions'] = reactions
            post['comments'] = comments

        return posts

    @api.multi
    def dit_show_likes(self):
        # Generates a random name between 9 and 15 characters long and writes it to the record.
        print 'hello ======================='

        api_key = 'Your_Api_key_Here'

        # Database connection
        url = 'http://localhost:8069'
        db = 'db_name'
        username = 'admin'
        password = 'pass'

        common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))

        uid = common.authenticate(db, username, password, {})

        models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

        graph = facebook.GraphAPI(access_token=api_key, version='2.9')

        posts = self.getPosts(25, graph)

        print 'posts'

        if 'data' in posts:

            for post in posts['data']:

                print post['reactions']['data']

                for reaction in post['reactions']['data']:
                    print reaction

                    if 'name' in reaction:
                        users_list = getUserFromDb(reaction['name'], models, common, db, uid, password)
                        updateUserLike(users_list, reaction, post, models, common, db, uid, password)

                for comment in post['comments']['data']:

                    if 'message' in comment:
                        if 'id' in comment:
                            if 'permalink_url' in comment:
                                if 'from' in comment:
                                    users_list = getUserFromDb(comment['from']['name'], models, common, db, uid,
                                                               password)
                                    updateUserComment(users_list, comment, post, models, common, db, uid, password)

        print 'reading comments'

        records = models.execute_kw(db, uid, password,
                                    'customer.facebook.comment', 'search_read', [[]],
                                    {'fields': ['comment_id', 'post_url', 'liker_id']})
        rec = {}
        for record in records:
            print record['comment_id']
            comment_id = record['comment_id']

            rec = models.execute_kw(db, uid, password,
                                    'customer.facebook.like', 'search_read',
                                    [[['post_url', '=', record['post_url']], ['liker_id', 'like', record['liker_id']]]],
                                    {'fields': ['liker_id', 'like_type', 'post_url']})

            print 'copuuuuuuuuuuuuuuuuuuuuunt'

            print rec
            if rec:
                models.execute_kw(db, uid, password, 'customer.facebook.comment', 'write', [record['id'],
                                                                                        {'liked': True,
                                                                                         'like_type': rec[0][
                                                                                             'like_type']}
                                                                                        ])

            obj_comm = {}
            print 'try'
            try:
                obj_comm = graph.get_object(comment_id)


            except Exception as e:
                print('Exception!!!')
                print e

            finally:
                if 'id' not in obj_comm:
                    # comment deleted : Update database
                    models.execute_kw(db, uid, password, 'customer.facebook.comment', 'write', [record['id'], {
                        'deleted': True
                    }])

        print 'reading comments finished'

        return {
            "name": "facebook",
            "type": "ir.actions.act_window",
            "res_model": "customer.facebook.like",
            "views": [[False, "form"], [False, "tree"]],
            "view_mode": "form,tree",
        }

class FacebookLike(models.Model):

    _name = "customer.facebook.like"

    post_url = fields.Char('post url')
    liker_id = fields.Char('liker id')
    like_type = fields.Char('reaction')
    customer_id = fields.Many2one('res.partner')


class FacebookComment(models.Model):

    _name = 'customer.facebook.comment'

    post_url = fields.Char('post url')
    comment_id = fields.Char('comment id')
    liker_id = fields.Char('liker_id')
    like_type = fields.Char('reaction')
    comment_url = fields.Char('comment url')
    message_str = fields.Text('message')
    deleted = fields.Boolean('deleted ?')
    liked = fields.Boolean('liked ?')
    customer_id = fields.Many2one('res.partner')