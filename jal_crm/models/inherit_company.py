from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import html2plaintext

class inheritedResCompany(models.Model):
   _inherit = "res.company"

   # ship_ids = fields.One2many('company.ship.add','mst_id',string="Ship Location")

   def _convert_html_to_text(self, html):
      if not html:
         return ""
      return html2plaintext(html or "")

# class Companyshipadd(models.Model):
#    _name = "company.ship.add"

#    mst_id = fields.Many2('res.company',string="MST")
   
#    street = fields.Char(string="Address")
#    street2 = fields.Char(string="Street2")
#    zip = fields.Char(string="Zip")
#    city_id = fields.Char(string="City")
#    state_id = fields.Many2one(
#         'res.country.state',
#         string="Fed. State", domain="[('country_id', '=?', country_id)]")
#    country_id = fields.Many2one('res.country',  string="Country")