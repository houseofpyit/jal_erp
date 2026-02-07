from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from num2words import num2words
from lxml import etree

class inheritHopSalebill(models.Model):
   _inherit = "hop.salebill"

   business_type = fields.Selection([("international", "International"), ("domestic", "Domestic"), ("trading", "Trading")],string="Business Type",tracking=True)

   @api.model
   def default_get(self, fields):
      res = super(inheritHopSalebill, self).default_get(fields)
      if self.env.context.get('default_business_type',False) == 'international':
         res['business_type'] = "international"
         res['is_export_bill'] = True
      if self.env.context.get('default_business_type',False) == 'domestic':
         res['business_type'] = "domestic"
      if self.env.context.get('default_business_type',False) == 'trading':
         res['business_type'] = "trading"
      return res
   
   @api.onchange('business_type')
   def _onchange_business_type(self):
      self.is_export_bill = False
      if self.business_type == 'international':
         self.is_export_bill = True
         
class inherithopsalebillline(models.Model):
   _inherit = "hop.salebill.line"

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