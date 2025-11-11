from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

    
class inheritedPurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    bucket = fields.Float(string='(Bucket/Bags/Pouch)',store=True)
    uom_handling_type = fields.Selection(related='product_id.uom_handling_type',string="UoM Handling Type",store=False)

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        res = super(inheritedPurchaseOrderLine, self)._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        res.update({'demand_bucket':self.bucket})
        return res