from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class inheritedPartner(models.Model):
   _inherit = "res.partner"
   
   @api.model
   def _get_default_team(self):
      return self.env['crm.team']._get_default_team_id()
   
   business_type = fields.Selection([("international", "International"), ("domestic", "Domestic"), ("trading", "Trading")],string="Business Type",tracking=True,default=lambda self: self.env.context.get('default_business_type',False))
   team_id = fields.Many2one('crm.team',string="Sales Team",domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",tracking=True,default=_get_default_team)

   # @api.onchange('team_id')
   # def _onchange_team_id(self):
   #    self.business_type = self.team_id.business_type