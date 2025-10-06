from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class inheritPurchaseRequisite(models.Model):
    _inherit = "jal.purchase.requisite"

    def create_purchase_po(self):
         line_list = []
         for line in self.line_ids:
            line_list.append((0,0,{
               'product_id': line.product_id.id,
               'product_qty':line.qty,
               'product_uom':line.uom_id.id,
               'date_planned': fields.Datetime.now(),
               'hsn_id':line.product_id.hsn_id.id,
               'price_unit': line.product_id.standard_price,
               'name': (f"{line.product_id.description_purchase}" if line.product_id.description_purchase else f"{line.product_id.display_name}"),
            }))
         return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'view_mode': 'form',
            'res_model': 'purchase.order', 
            'context': {'default_pur_req_id': self.id,'default_order_line':line_list},
            'target': 'current', 
         }