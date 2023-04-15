# In sale_order.py or a new custom module
from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    consignment_count = fields.Integer(string='Consignment Count', compute='_compute_consignment_count')

 

    def create_custom_invoice(self, custom_invoice_lines):
        """
        custom_invoice_lines: A list of tuples (order_line_id, invoice_qty)
        """
    
        self.ensure_one()
        invoice_lines_vals = []

        for line, invoice_qty in custom_invoice_lines:
            invoice_line_vals = line._prepare_invoice_line(quantity=invoice_qty)
            invoice_lines_vals.append((0, 0, invoice_line_vals))

        invoice_vals = {
            'ref': self.client_order_ref,
            'move_type': 'out_invoice',
            'narration': self.note,
            'currency_id': self.currency_id.id,
            'invoice_user_id': self.user_id and self.user_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'fiscal_position_id': self.fiscal_position_id.id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': invoice_lines_vals,
            'team_id': self.team_id.id,
        }

        invoice = self.env['account.move'].create(invoice_vals)
        invoice.action_post()
        return invoice
    
    def action_view_consignment(self):
        self.ensure_one()
        action = self.env.ref("consignment.action_consignment_invoicing").read()[0]
        action["domain"] = [("sale_order_ids", "in", [self.id])]
        return action
    
    def create_remaining_invoice(self):
        self.ensure_one()
        # Get the list of products that have already been invoiced
        invoiced_product_ids = [line.product_id.id for invoice in self.invoice_ids for line in invoice.invoice_line_ids]

        # Find the remaining order lines to invoice
        remaining_order_lines = self.order_line.filtered(lambda line: line.product_id.id not in invoiced_product_ids)

        # Create a list of tuples (order_line, invoice_qty)
        custom_invoice_lines = [(line, line.product_uom_qty) for line in remaining_order_lines]

        # Create the invoice for the remaining products
        invoice = self.create_custom_invoice(custom_invoice_lines)

        # Return an action to display the new invoice
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        action['res_id'] = invoice.id
        return action
