from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date,datetime

class InheriteStockPicking(models.Model):
    _inherit = "stock.picking"

    vendor_bill_no = fields.Char(string="Vendor Bill No.")
    vendor_bill_date = fields.Date(string="Vendor Bill Date")
    vehicle_no = fields.Char(string="Vehicle No")

    @api.onchange('vendor_bill_no')
    def _onchange_vendor_bill_no(self):
        if self.vendor_bill_no:
            domain = [
                ('partner_id', '=', self.partner_id.id),
                ('vendor_bill_no', '=', self.vendor_bill_no),
            ]

            if self.env.user.fy_year_id:
                domain.append(('vendor_bill_date', '>=', self.env.user.fy_from_date))
                domain.append(('vendor_bill_date', '<=', self.env.user.fy_to_date))

            picking_rec = self.env['stock.picking'].search(domain)

            if picking_rec:
                raise UserError(_("This Vendor Bill Number is already generated for this Vendor"))