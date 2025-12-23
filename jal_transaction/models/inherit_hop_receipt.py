from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class inheritHopReceipt(models.Model):
    _inherit = "hop.receipt"

    sale_id = fields.Many2one('sale.order',string="Sale Order")