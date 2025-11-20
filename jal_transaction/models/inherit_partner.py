from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class inheritedPartner(models.Model):
   _inherit = "res.partner"
   
   msme_type = fields.Selection([('yes','Yes'),('no','No')],string='MSME Type',tracking=True)