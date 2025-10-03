from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class inheritedCrmTeam(models.Model):
   _inherit = "crm.team"
   
   business_type = fields.Selection([("international", "International"), ("domestic", "Domestic"), ("trading", "Trading")],string="Business Type",tracking=True,default=lambda self: self.env.user.crm_team_id.business_type)