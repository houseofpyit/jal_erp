from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class inheritedProductTemplate(models.Model):
   _inherit = "product.template"
   
   cost_id = fields.Many2one('hop.cost.center',string="Cost Center")
