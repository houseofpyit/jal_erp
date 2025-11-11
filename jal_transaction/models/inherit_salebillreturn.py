from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from num2words import num2words
from lxml import etree

class inheritHopSaleBillReturn(models.Model):
   _inherit = "hop.salebillreturn"

   business_type = fields.Selection([("international", "International"), ("domestic", "Domestic"), ("trading", "Trading")],string="Business Type",tracking=True)