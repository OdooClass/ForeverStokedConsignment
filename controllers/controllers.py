# -*- coding: utf-8 -*-
# from odoo import http


# class Consignment(http.Controller):
#     @http.route('/consignment/consignment', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/consignment/consignment/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('consignment.listing', {
#             'root': '/consignment/consignment',
#             'objects': http.request.env['consignment.consignment'].search([]),
#         })

#     @http.route('/consignment/consignment/objects/<model("consignment.consignment"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('consignment.object', {
#             'object': obj
#         })
