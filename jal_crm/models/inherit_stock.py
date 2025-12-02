from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date,datetime

class InheriteStockPicking(models.Model):
    _inherit = "stock.picking"

    vendor_bill_no = fields.Char(string="Vendor Bill No.")
    vendor_bill_date = fields.Date(string="Vendor Bill Date")
    vehicle_no = fields.Char(string="Vehicle No")