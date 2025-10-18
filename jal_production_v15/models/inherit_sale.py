from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class InheritSale(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(InheritSale, self).action_confirm()
        for line in self.order_line:
            stock_move = self.env['stock.move'].search([('sale_line_id', '=', line.id)])
            stock_move.write({'demand_bucket': line.bucket})
        return res
    
class inheritedSaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    grade_id = fields.Many2one('product.attribute.value',string="Grade",domain="[('attribute_id.attribute_type','=','grade')]")
    mesh_id = fields.Many2one('product.attribute.value',string="Mesh",domain="[('attribute_id.attribute_type','=','mesh')]")
    bucket = fields.Float(string='Bucket',store=True)