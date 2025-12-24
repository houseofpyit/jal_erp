from odoo import api, models, fields
from datetime import date,datetime
from odoo.exceptions import ValidationError

class PurchaseOrderReportWiz(models.TransientModel):
    _name = 'purchase.order.report.wiz'
    _description= "Purchase Order Report Wiz"

    # rpt_xls_file = fields.Binary()
    from_date = fields.Date(string="From Date",default=fields.Date.context_today)
    to_date = fields.Date(string="To Date",default=fields.Date.context_today)
    partner_ids = fields.Many2many('res.partner',string="Vendors")
    company_id = fields.Many2one('res.company',string="Company" , default=lambda self: self.env.company)

    @api.onchange('from_date', 'to_date')
    def _onchange_dates(self):
        for rec in self:
            if rec.from_date and rec.to_date and rec.to_date < rec.from_date:
                rec.to_date = False
                return {
                    'warning': {
                        'title': ("Invalid Date"),
                        'message': ("To Date cannot be earlier than From Date."),
                    }
                }
            
    def purchase_vals_data(self):
        self.ensure_one()

        domain = [
            ('state', 'in', ['purchase', 'done']),
            ('company_id', '=', self.company_id.id),]

        if self.from_date:
            domain.append(('date_order', '>=', self.from_date))
        if self.to_date:
            domain.append(('date_order', '<=', self.to_date))
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))

        orders = self.env['purchase.order'].search(domain)

        result = {}

        for order in orders:
            po_name = order.id
            vendor = order.partner_id.id
            order_date = order.date_order.date()

            for line in order.order_line:
                if not line.product_id:
                    continue

                key = (po_name,vendor, order_date, line.product_id.id)

                if key not in result:
                    result[key] = {
                        'po_id': order.id,
                        'po_name': po_name,
                        'vendor_id': order.partner_id.id,
                        'vendor': vendor,
                        'date': order_date,
                        'product': line.product_id.display_name,
                        'product_id': line.product_id.id,
                        'ordered_qty': 0.0,
                        'received_qty': 0.0,
                        'pending_qty': 0.0,
                    }

                ordered = line.product_qty
                received = line.qty_received
                pending = ordered - received

                result[key]['ordered_qty'] += ordered
                result[key]['received_qty'] += received
                result[key]['pending_qty'] += pending

        return list(result.values())
    

    def genrate_purchase_report(self):
        self.env['order.view.report.wiz'].search([]).unlink()
        data_vals = self.purchase_vals_data()
        if not data_vals:
            raise ValidationError("Data Not Found !!!")
        
        for rec in data_vals:
            self.env['order.view.report.wiz'].create({
                    'purchase_id': rec.get('po_id'),
                    'partner_id': rec.get('vendor_id') if rec.get('vendor_id') else None,
                    'date': rec.get('date') if rec.get('date') else None,
                    'product_id': rec.get('product_id') if rec.get('product_id') else None,
                    'ordered_qty': rec.get('ordered_qty') if rec.get('ordered_qty') else 0,
                    'received_qty': rec.get('received_qty') if rec.get('received_qty') else 0,
                    'pending_qty': rec.get('pending_qty') if rec.get('pending_qty') else 0,
                })

        return {
                'type': 'ir.actions.act_window',
                'name': 'Purchase Order Report',
                'view_mode': 'tree',
                'res_model': 'order.view.report.wiz', 
                'target': 'current', 
                'context': "{'create': False}",
                'help': """
                <p class="o_view_nocontent_smiling_face">
                    {}
                """.format(('There is no data for Purchase Order')),
            }

class OrderViewReportWiz(models.TransientModel):
    _name = "order.view.report.wiz"
    _description = 'Order View Report Wiz'
    _order = "id desc"

    purchase_id = fields.Many2one('purchase.order', string='Purchase')
    date = fields.Date(string='Date')
    partner_id = fields.Many2one('res.partner', string='Vendor')
    product_id = fields.Many2one('product.product',string='Product')
    ordered_qty = fields.Float(string='Ordered Qty')
    received_qty = fields.Float(string='Received Qty')
    pending_qty = fields.Float(string='Pending Qty')
