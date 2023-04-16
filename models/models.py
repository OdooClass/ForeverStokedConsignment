from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ConsignmentInvoicing(models.Model):
    _name = "consignment.invoicing"
    _description = "Consignment Invoicing"

    partner_id = fields.Many2one("res.partner", string="Customer", required=True)
    line_ids = fields.One2many("consignment.invoicing.lineitem", "invoicing_id", string="Line Items")
    sale_order_ids = fields.Many2many("sale.order", string="Sales Orders")
    invoice_ids = fields.Many2many("account.move", string="Invoices")

    state = fields.Selection([
        ("draft", "Draft"),
        ("done", "Done"),
    ], string="Status", readonly=True, default="draft")

    name = fields.Char(string="Reference", required=True, default="/", readonly=True)
    # Other fields

    @api.model
    def create(self, vals):
        if vals.get("name", "/") == "/":
            vals["name"] = self.env["ir.sequence"].next_by_code("consignment.invoicing") or "/"
        return super(ConsignmentInvoicing, self).create(vals)
    
    def button_post(self):
        self.ensure_one()
        self.process_consignment_invoicing()


    def fetch_products(self):
        self.ensure_one()

        ConsignmentInvoicingLineItem = self.env['consignment.invoicing.lineitem']
        SaleOrderLine = self.env['sale.order.line']

        # Find all products in the consignment.invoicing.lineitem model
        consignment_product_ids = {line.product_id.id for line in self.line_ids}

        sale_order_lines = self.env['sale.order.line'].search([
            ('product_id', 'not in', list(consignment_product_ids)),
            ("state", "in", ["sale", "done"]),
            ("invoice_status", "=", "to invoice"),
            ('order_id.partner_id', '=', self.partner_id.id),
        ])

        added_products = set()  # Keep track of added products

        for line in sale_order_lines:
            if (line.qty_invoiced < line.product_uom_qty) and (line.product_id.id not in added_products):
                invoice_ids = line.order_id.invoice_ids.filtered(lambda inv: inv.partner_id == self.partner_id.id)
                if not invoice_ids:
                    new_line = {
                        'invoicing_id': self.id,
                        'product_id': line.product_id.id,
                        'quantity': 0,
                    }
                    ConsignmentInvoicingLineItem.create(new_line)
                    added_products.add(line.product_id.id)  # Mark product as added

    def process_consignment_invoicing(self):
        self.ensure_one()

        if not self.line_ids:
            raise UserError(_("Please add some line items before processing."))

        SaleOrder = self.env["sale.order"]
        open_orders = SaleOrder.search([
            ("partner_id", "=", self.partner_id.id),
            ("state", "in", ["sale", "done"]),
            ("invoice_status", "=", "to invoice"),
        ], order="date_order")

        if not open_orders:
            raise UserError(_("No open sales orders found for this customer."))

        product_qty_to_invoice = {}

        # First loop to calculate the total quantity to invoice
        for line in self.line_ids:
            open_order_lines = open_orders.mapped("order_line").filtered(
                lambda ol: ol.product_id == line.product_id and not ol.is_downpayment
            )

            total_open_qty = sum(open_order_lines.mapped("qty_to_invoice"))

            product_qty_to_invoice[line.product_id] = total_open_qty - line.quantity

        # Prepare the custom_invoice_lines list outside the product loop
        custom_invoice_lines = []

        # Iterate over the products to create a single invoice
        for product, qty_to_invoice in product_qty_to_invoice.items():
            remaining_qty = qty_to_invoice

            for order in open_orders:
                order_lines = order.order_line.filtered(lambda ol: ol.product_id == product and not ol.is_downpayment)

                for line in order_lines:
                    if remaining_qty <= 0:
                        break

                    invoice_qty = min(line.qty_to_invoice, remaining_qty)
                    remaining_qty -= invoice_qty

                    if invoice_qty > 0:
                        custom_invoice_lines.append((line, invoice_qty))

                if remaining_qty <= 0:
                    break

        # Create and post the invoice outside the product loop
        if custom_invoice_lines:
            open_orders[0].create_custom_invoice(custom_invoice_lines)

        #self.write({"state": "done"})
        self.write({"state": "done", "sale_order_ids": [(6, 0, open_orders.ids)]})
        return True


class ConsignmentInvoicingLineItem(models.Model):
    _name = "consignment.invoicing.lineitem"
    _description = "Consignment Invoicing Line Item"

    invoicing_id = fields.Many2one("consignment.invoicing", string="Invoicing", required=True, ondelete="cascade")
    product_id = fields.Many2one("product.product", string="Product", required=True)
    quantity = fields.Float(string="Quantity", required=True, default=0)
    product_qty_to_invoice = fields.Float(string='Qty to Invoice', compute='_compute_product_qty_to_invoice', store=True)

    @api.depends('product_id')
    def _compute_product_qty_to_invoice(self):
        for line in self:
            if line.product_id:
                self.env.cr.execute("""
                    SELECT
                        sum(qty_to_invoice) as total_qty_to_invoice
                    FROM
                        sale_order_product_by_customer
                    WHERE
                        product_id = %s
                """, (line.product_id.id,))
                result = self.env.cr.fetchone()
                line.product_qty_to_invoice = result[0] if result else 0
                
    def action_view_sales_orders(self):
        self.ensure_one()
        action = self.env.ref('sale.action_orders').read()[0]
        action['domain'] = [
            ('order_line.product_id', '=', self.product_id.id),
            ('state', 'not in', ('cancel', 'done'))
        ]
        action['context'] = {
            'search_default_product_id': self.product_id.id,
            'search_default_qty_to_invoice': True
        }
        return action
    
class ResPartner(models.Model):
    _inherit = 'res.partner'

    def action_view_consignments(self):
        self.ensure_one()
        action = self.env.ref('consignment.action_consignment_invoicing').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        return action
