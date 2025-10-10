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

   business_type = fields.Selection([("international", "International"), ("domestic", "Domestic"), ("trading", "Trading")],string="Business Type",tracking=True,default=lambda self: self.env.context.get('default_business_type',False))
   continent_type = fields.Selection([('africa', 'Africa'),('antarctica', 'Antarctica'),('asia', 'Asia'),('europe', 'Europe'),('north_america', 'North America'),('oceania', 'Oceania'),('south_america', 'South America'),],string="Continent")
   quantity = fields.Float(string="Quantity",tracking=True)
   unit_id = fields.Many2one('uom.uom',string="Unit")
   unit_price = fields.Monetary(string="Unit Price",currency_field='company_currency')

   # @api.onchange('team_id')
   # def _onchange_team_id(self):
   #    self.business_type = self.team_id.business_type

   @api.onchange('quantity','unit_price')
   def _onchange_quantity(self):
      self.expected_revenue = self.quantity * self.unit_price
   
   @api.depends('country_id')
   @api.onchange('country_id')
   def _onchange_country_id(self):
      self.continent_type = self.country_id.continent_type

   def action_sale_quotations_new(self):
      res = super(inheritedCRM, self).action_sale_quotations_new()
      res['context'].update({'default_business_type': self.business_type})
      return res

   