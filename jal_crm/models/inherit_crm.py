from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

AVAILABLE_PRIORITIES = [
   #  ('0', 'Low'),
    ('0', 'Hot'),
    ('1', 'Mild'),
    ('2', 'Cold'),
    ('3', ''),
]


class inheritedCRM(models.Model):
   _inherit = "crm.lead"

   priority = fields.Selection(
        AVAILABLE_PRIORITIES, string='Priority', index=True,
        default=AVAILABLE_PRIORITIES[0][0])

   business_type = fields.Selection([("international", "International"), ("domestic", "Domestic"), ("trading", "Trading")],string="Business Type",tracking=True,default=lambda self: self.env.user.crm_team_id.business_type)
   continent_type = fields.Selection([('africa', 'Africa'),('antarctica', 'Antarctica'),('asia', 'Asia'),('europe', 'Europe'),('north_america', 'North America'),('oceania', 'Oceania'),('south_america', 'South America'),],string="Continent")
   quantity = fields.Char(string="Quantity",tracking=True)

   @api.onchange('team_id')
   def _onchange_team_id(self):
      self.business_type = self.team_id.business_type

   @api.depends('country_id')
   @api.onchange('country_id')
   def _onchange_country_id(self):
      self.continent_type = self.country_id.continent_type

   