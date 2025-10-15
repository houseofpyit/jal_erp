from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class inheritedProductAttribute(models.Model):
   _inherit = "product.attribute"

   attribute_type = fields.Selection([('grade', 'Grade'),('mesh', 'Mesh'),('bucket', 'Bucket')], string='Attribute Type')