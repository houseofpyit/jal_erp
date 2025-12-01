from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError


class ProductShippingMst(models.Model):
    _name = 'product.shipping.mst'
    _description = 'Product Label'
    _inherit = ['mail.thread']
    _order = 'id desc'
    

    name = fields.Char(string='Name',tracking=True)
    display_name_on_pi = fields.Selection([
        ("product_name", "Product Name"),  
        ("shipping_name", "Shipping Name")],string="Label Type",tracking=True)
