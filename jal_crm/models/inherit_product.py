from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class inheritedProductTemplate(models.Model):
   _inherit = "product.template"
   
   @api.model
   def _get_default_team(self):
      return self.env['crm.team']._get_default_team_id()
   
   business_type = fields.Selection([("international", "International"), ("domestic", "Domestic"), ("trading", "Trading")],string="Business Type",tracking=True,default=lambda self: self.env.user.crm_team_id.business_type)
   team_id = fields.Many2one('crm.team',string="Sales Team",domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",tracking=True,default=_get_default_team)
   un_number = fields.Char(string="UN Number",tracking=True)
   is_packing = fields.Boolean('Packing',tracking=True)
   is_shipping = fields.Boolean('Is Shipping Name/Label',tracking=True)
   drum_cap_id = fields.Many2one('capacity.mst',string="Capacity Per Drum")

   @api.onchange('team_id')
   def _onchange_team_id(self):
      self.business_type = self.team_id.business_type