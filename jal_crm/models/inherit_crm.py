from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta, date

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
        default=AVAILABLE_PRIORITIES[3][0])

   business_type = fields.Selection([("international", "International"), ("domestic", "Domestic"), ("trading", "Trading")],string="Business Type",tracking=True,default=lambda self: self.env.context.get('default_business_type',False))
   continent_type = fields.Selection([('africa', 'Africa'),('antarctica', 'Antarctica'),('asia', 'Asia'),('europe', 'Europe'),('north_america', 'North America'),('oceania', 'Oceania'),('south_america', 'South America'),],string="Continent")
   quantity = fields.Float(string="Quantity",tracking=True)
   unit_id = fields.Many2one('uom.uom',string="Unit")
   unit_price = fields.Monetary(string="Unit Price",currency_field='company_currency')
   company_currency = fields.Many2one('res.currency',string="Currency",store=True,readonly=False)
   is_stage = fields.Boolean('Is Stage', compute="compute_is_stage")

   def default_get(self, fields):
      res = super(inheritedCRM, self).default_get(fields)
      if self.env.context.get('default_business_type',False) == 'international':
         res['company_currency'] = self.env.ref('base.USD').id
         res['unit_id'] = self.env['uom.uom'].search([('name', '=', 'MT')], limit=1).id
      else:
         res['company_currency'] = self.env.company.currency_id.id
         res['unit_id'] = self.env.ref('uom.product_uom_kgm').id

      res['date_deadline'] = date.today() + timedelta(days=15)
      return res

   @api.depends('create_date')
   def compute_is_stage(self):
      SaleOrder = self.env['sale.order']
      Stage = self.env['crm.stage']

      default_stage = Stage.search([('name', '=', 'New')], limit=1)
      quotation_stage = Stage.search([('is_quotation', '=', True)], limit=1)
      proforma_stage = Stage.search([('is_performa', '=', True)], limit=1)
      won_stage = Stage.search([('is_won', '=', True)], limit=1)
      lost_stage = Stage.search([('is_lost', '=', True)], limit=1)

      today = fields.Datetime.now()

      for rec in self:
         stage_id = default_stage.id if default_stage else False

         sale = SaleOrder.search([('opportunity_id', '=', rec.id)], limit=1)

         if sale:
               if sale.state == 'draft':
                  stage_id = quotation_stage.id

               elif sale.state == 'create_pi':
                  stage_id = proforma_stage.id

               elif sale.state == 'sale':
                  stage_id = won_stage.id

         else:
               if rec.create_date and today - rec.create_date >= timedelta(days=15):
                  stage_id = lost_stage.id

         rec.stage_id = stage_id
         rec.is_stage = True



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
      res['context'].update({'default_business_type': self.business_type
                             ,'default_currency_id': self.company_currency.id
                             ,'default_jal_currency_id': self.company_currency.id})
      return res
   
   @api.model
   def create(self, vals):
      if 'priority' in vals:
         if not vals.get('priority') or vals.get('priority') == '3':
               raise ValidationError(_("Priority cannot be blank. Please select Hot, Mild, or Cold."))
      return super(inheritedCRM, self).create(vals)


   def write(self, vals):
      if 'priority' in vals:
         if not vals.get('priority') or vals.get('priority') == '3':
               raise ValidationError(_("Priority cannot be blank. Please select Hot, Mild, or Cold."))
      return super(inheritedCRM, self).write(vals)

   
class inheritedCRMStage(models.Model):
   _inherit = "crm.stage"

   is_performa = fields.Boolean('Is Performa Stage?')
   is_quotation = fields.Boolean('Is Quotation Stage?')
   is_lost = fields.Boolean('Is Lost Stage?')

   @api.onchange('is_performa','is_quotation','is_lost','is_won')
   def _onchange_is_performa(self):
      if self.is_performa:
         record = self.search([('is_performa', '=', True)])
         if record:
               self.is_performa = False
               return {
                  'warning': {
                     'title': "Validation",
                     'message': f"The stage '{record.name}' is already marked as a Performa stage. Only one stage can have Performa enabled.",
                  }
               }
         
      if self.is_quotation:
         record = self.search([('is_quotation', '=', True)])
         if record:
               self.is_quotation = False
               return {
                  'warning': {
                     'title': "Validation",
                     'message': f"The stage '{record.name}' is already marked as a Quotation stage. Only one stage can have Quotation enabled.",
                  }
               }
         
      if self.is_lost:
         record = self.search([('is_lost', '=', True)])
         if record:
               self.is_lost = False
               return {
                  'warning': {
                     'title': "Validation",
                     'message': f"The stage '{record.name}' is already marked as a Lost stage. Only one stage can have Lost enabled.",
                  }
               }
         
      if self.is_won:
         record = self.search([('is_won', '=', True)])
         if record:
               self.is_won = False
               return {
                  'warning': {
                     'title': "Validation",
                     'message': f"The stage '{record.name}' is already marked as a Won stage. Only one stage can have Won enabled.",
                  }
               }