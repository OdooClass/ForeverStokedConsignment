from odoo import models, fields, api

class SaleOrderProductByCustomer(models.Model):
    _name = 'sale.order.product.by.customer'
    _description = 'Sale Order Products by Customer'
    _auto = False

    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    order_id = fields.Many2one('sale.order', string='Sales Order', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    product_uom_qty = fields.Float('Quantity', readonly=True)
    qty_to_invoice = fields.Float('Qty to Invoice', readonly=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)

    @api.model
    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW sale_order_product_by_customer AS (
                SELECT
                    min(sol.id) as id,
                    so.partner_id as partner_id,
                    sol.order_id as order_id,
                    sol.product_id as product_id,
                    sum(sol.product_uom_qty) as product_uom_qty,
                    sum(sol.qty_to_invoice) as qty_to_invoice,
                    am.id as invoice_id
                FROM
                    sale_order_line sol
                    JOIN sale_order so ON sol.order_id = so.id
                    LEFT JOIN sale_order_line_invoice_rel rel ON rel.order_line_id = sol.id
                    LEFT JOIN account_move_line aml ON aml.id = rel.invoice_line_id
                    LEFT JOIN account_move am ON am.id = aml.move_id AND am.state != 'cancel'
                WHERE
                    so.state NOT IN ('cancel', 'done')
                GROUP BY
                    so.partner_id,
                    sol.order_id,
                    sol.product_id,
                    am.id
            )
        """)
