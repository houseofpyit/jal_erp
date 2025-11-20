from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class inheritedPurchaseOrder(models.Model):
   _inherit = "purchase.order"
   
   @api.model
   def _get_default_team(self):
      return self.env['crm.team']._get_default_team_id()
   
   business_type = fields.Selection([("international", "International"), ("domestic", "Domestic"), ("trading", "Trading")],string="Business Type",tracking=True,default=lambda self: self.env.user.crm_team_id.business_type)
   team_id = fields.Many2one('crm.team',string="Sales Team",domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",tracking=True,default=_get_default_team)
   pur_req_id = fields.Many2one('jal.purchase.requisite',string="Purchase Requisition")
   attachment_ids = fields.Many2many('ir.attachment','attachment_po_id',string="Document Attachment")
   # remarks = fields.Text(string="Remarks")
   conditions_id = fields.Many2one('sale.term.conditions',string="Term & Conditions",tracking=True)

   @api.onchange('conditions_id')
   def _onchange_conditions_id(self):
      self.notes = self.conditions_id.note

   @api.onchange('team_id')
   def _onchange_team_id(self):
      self.business_type = self.team_id.business_type
