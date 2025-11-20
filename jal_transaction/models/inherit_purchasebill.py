from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class inheritPurchaseBill(models.Model):
    _inherit = "hop.purchasebill"

    attachment_ids = fields.Many2many('ir.attachment','attachment_pur_bill_id',string="Document Attachment")