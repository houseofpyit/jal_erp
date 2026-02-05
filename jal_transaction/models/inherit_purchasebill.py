from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class inheritPurchaseBill(models.Model):
    _inherit = "hop.purchasebill"

    attachment_ids = fields.Many2many('ir.attachment','attachment_pur_bill_id',string="Document Attachment")
    picking_id = fields.Many2one('stock.picking',string='Grn No.')

class inheritPurchaseBillLine(models.Model):
    _inherit = "hop.purchasebill.line"

    pcs = fields.Float("PCS",digits=(2, 3))
    
    @api.model
    def create(self, vals):
        if vals.get('pcs', 0) <= 0:
            raise ValidationError("Quantity cannot be zero. Please correct the product details.")
        return super().create(vals)
    
    def write(self, vals):
      if 'pcs' in vals:
         if vals.get('pcs', 0) <= 0:
            raise ValidationError("Quantity cannot be zero or negative. Please correct the product details.")
      return super().write(vals)