from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class inheritPurchaseReturnLine(models.Model):
    _inherit = "hop.purchasebillreturn.line"

    pcs = fields.Float("PCS",digits=(2, 3))