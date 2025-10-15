from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class inheritedSaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    grade_id = fields.Many2one('product.attribute.value',string="Grade",domain="[('attribute_id.attribute_type','=','grade')]",tracking=True)
    mesh_id = fields.Many2one('product.attribute.value',string="Mesh",domain="[('attribute_id.attribute_type','=','mesh')]",tracking=True)