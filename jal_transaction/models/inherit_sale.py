from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class inheritSaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    @api.onchange('product_template_id')
    def _onchange_product_template_id(self):
        if self.product_template_id:
            self.hsn_id = self.product_template_id.hsn_id.id
            self.price_unit = self.product_template_id.list_price
            if self.order_id.partner_id.disc:
                self.disc_per = self.order_id.partner_id.disc
                