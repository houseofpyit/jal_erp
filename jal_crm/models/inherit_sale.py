from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from num2words import num2words
from lxml import etree

class inheritedSaleOrder(models.Model):
   _inherit = "sale.order"

   def _get_default_order_chr(self,company_id=False,ord_date= False, bill_chr=False):
      order_chr = "SO"
      if self.env.context.get('default_business_type',False) == 'international':
         order_chr = "SO/INT/"
      if self.env.context.get('default_business_type',False) == 'domestic':
         order_chr = "SO/DOM/"
      if self.env.context.get('default_business_type',False) == 'trading':
         order_chr = "SO/TRD/"
      return order_chr
   
   business_type = fields.Selection([("international", "International"), ("domestic", "Domestic"), ("trading", "Trading")],string="Business Type",tracking=True,default=lambda self: self.env.user.crm_team_id.business_type)
   terms_id = fields.Many2one('sale.terms.mst',string="Delivery terms",tracking=True)
   incoterm_id = fields.Many2one('sale.incoterm.mst',string="Incoterm ",tracking=True)
   port_id = fields.Many2one('sale.port.mst',string="Destination Port",tracking=True)
   country_id = fields.Many2one('res.country',string="Country",tracking=True)
   bank_id = fields.Many2one('bank.mst',string="Bank",tracking=True)
   conditions_id = fields.Many2one('sale.term.conditions',string="Term & Conditions",tracking=True)
   palletized_type = fields.Selection([("Yes", "Yes"), ("No", "No")],string="Palletized",tracking=True)
   lead_count = fields.Integer(string="Lead Count", copy=False,help="Count of the created sale for lead")
   state = fields.Selection(selection_add=[ ('draft','Quotation'),
                                            ('quotation_confirm','Quotation confirm'),
                                            ('create_pi','Create PI'),
                                            ('sale', 'Confirm PI')],tracking=True)
   po_no = fields.Char(string="PO",tracking=True)
   po_date = fields.Date(string="PO Date",tracking=True)
   reference = fields.Char(string="Reference",tracking=True)
   freight = fields.Char(string="Total Freight",tracking=True)
   insurance = fields.Char(string="Total Insurance",tracking=True)
   fob_rates = fields.Char(string="FOB Rates",tracking=True)
   inspection_id = fields.Many2one('sale.inspection.mst',string="Pre-Shipment Inspection",tracking=True)
   lading_type = fields.Selection([('house_bl','House BL'),
                              ('master_bl','Master BL')],string="Bill of Lading Type",tracking=True)
   purchase_req_count = fields.Integer(string="Purchase Requisition Count", copy=False)

   # @api.onchange('team_id')
   # def _onchange_team_id(self):
   #    self.business_type = self.team_id.business_type


   def amount_to_text(self, amount, currency='INR'):
      word = num2words(amount, lang='en_IN').upper()
      word = word.replace(",", " ")
      return word
   
   @api.onchange('conditions_id')
   def _onchange_conditions_id(self):
      self.note = self.conditions_id.note

   @api.onchange('partner_id')
   def _onchange_partner_id(self):
      self.country_id = self.partner_id.country_id.id

   @api.depends('company_id.account_fiscal_country_id', 'fiscal_position_id.country_id', 'fiscal_position_id.foreign_vat')
   def _compute_tax_country_id(self):
      res = super(inheritedSaleOrder, self)._compute_tax_country_id()
      for line in self:
         line.lead_count = len(self.env['crm.lead'].search([('id', '=', line.opportunity_id.id)]))
         line.purchase_req_count = len(self.env['jal.purchase.requisite'].search([('sale_id', '=', line.id)]))
      return res
   
   def create_purchase_requisite(self):
         line_list = []
         for line in self.order_line:
            line_list.append((0,0,{
               'product_id': line.product_id.id,
               'qty':line.product_uom_qty,
               'uom_id':line.product_id.uom_po_id.id,
            }))
         return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Requisition',
            'view_mode': 'form',
            'res_model': 'jal.purchase.requisite', 
            'context': {'default_sale_id': self.id,'default_user_id':self.env.user.id,'default_line_ids':line_list},
            'target': 'current', 
         }
            
   def action_view_lead(self):
      lead_rec = self.env['crm.lead'].search([('id', '=', self.opportunity_id.id)])
      return {
         'type': 'ir.actions.act_window',
         'name': 'Lead',
         'view_mode': 'form',
         'res_model': 'crm.lead',
         'res_id': lead_rec.id,
         'context': {'create': False}
         }
   
   def action_view_pur_req(self):
      pur_rec = self.env['jal.purchase.requisite'].search([('sale_id', '=', self.id)])
      return {
         'type': 'ir.actions.act_window',
         'name': 'Purchase Requisition',
         'view_mode': 'form',
         'res_model': 'jal.purchase.requisite',
         'res_id': pur_rec.id,
         'context': {'create': False}
         }
   
   def action_quotation_confirm(self):
      self.state = 'quotation_confirm'

   def action_create_pi(self):
      self.state = 'create_pi'

class inheritedSaleOrderLine(models.Model):
   _inherit = "sale.order.line"

   shipping_id = fields.Many2one('product.shipping.mst',string="Product Shipping")
   drum_cap_id = fields.Many2one('capacity.mst',string="Capacity Per Drum",domain="[('packaging_type','=','drum')]")
   bucket_cap_id = fields.Many2one('capacity.mst',string="Capacity Per Bucket",domain="[('packaging_type','=','bucket')]")
   box_cap_id = fields.Many2one('capacity.mst',string="Capacity Per Box",domain="[('packaging_type','=','box')]")
   pouch_id = fields.Many2one('pouch.name.mst',string="Pouch Name")
   name_id = fields.Many2one('name.mst',string="Name")
   lid_id = fields.Many2one('lid.color.mst',string="Lid Color")
   branding_id = fields.Many2one('branding.mst',string="Branding")
   box_id = fields.Many2one('box.color.mst',string="Box Color")
   drum_color_id = fields.Many2one('drum.color.mst',string="Drum Color")
   scoops_id = fields.Many2one('scoops.mst',string="Scoops")
   outer_id = fields.Many2one('outer.cartoons.mst',string="Outer Cartoons")
   packing_type = fields.Selection([("drum", "Drum"), ("bucket", "Bucket"),("usa_bucket", "USA-Bucket"), ("pouch", "Pouch")],string="Packing Type")
   packing_name = fields.Text(string="Packing Description")
   is_des = fields.Boolean(string="Is Packing Description", compute="_compute_packing_name", store=True)
      
   @api.depends(
      'packing_type', 'name_id', 'drum_cap_id', 'bucket_cap_id', 'box_cap_id',
      'branding_id', 'lid_id', 'drum_color_id', 'box_id', 'pouch_id',
      'scoops_id', 'outer_id'
   )
   @api.onchange(
      'packing_type', 'name_id', 'drum_cap_id', 'bucket_cap_id', 'box_cap_id',
      'branding_id', 'lid_id', 'drum_color_id', 'box_id', 'pouch_id',
      'scoops_id', 'outer_id'
   )
   def _compute_packing_name(self):
      for rec in self:
         description_lines = []

         if rec.packing_type == "drum":
               if rec.name_id:
                  description_lines.append(f"Name: {rec.name_id.name}")

               if rec.drum_cap_id:
                  cap = rec.drum_cap_id
                  description_lines.append(
                     f"Capacity per Drum: {cap.weight} Net {cap.uom_id.name} per Drum"
                  )

               if rec.branding_id:
                  description_lines.append(f"Branding: {rec.branding_id.name}")

         elif rec.packing_type == "bucket":
               if rec.name_id:
                  description_lines.append(f"Name: {rec.name_id.name}")

               if rec.bucket_cap_id:
                  cap = rec.bucket_cap_id
                  description_lines.append(
                     f"Capacity per Bucket: {cap.weight} Net {cap.uom_id.name} per Bucket"
                  )

               if rec.branding_id:
                  description_lines.append(f"Branding: {rec.branding_id.name}")

               if rec.lid_id:
                  description_lines.append(f"Lid Colour: {rec.lid_id.name}")

               if rec.drum_color_id:
                  description_lines.append(f"Drum Colour: {rec.drum_color_id.name}")

         elif rec.packing_type == "usa_bucket":
               if rec.name_id:
                  description_lines.append(f"Name: {rec.name_id.name}")

               if rec.bucket_cap_id:
                  cap = rec.bucket_cap_id
                  description_lines.append(
                     f"Capacity per USA-Bucket: {cap.weight} Net {cap.uom_id.name} per USA-Bucket"
                  )

               if rec.branding_id:
                  description_lines.append(f"Branding: {rec.branding_id.name}")

               if rec.lid_id:
                  description_lines.append(f"Lid Colour: {rec.lid_id.name}")

               if rec.drum_color_id:
                  description_lines.append(f"Drum Colour: {rec.drum_color_id.name}")

               if rec.scoops_id:
                  description_lines.append(f"Scoops: {rec.scoops_id.name}")

               if rec.outer_id:
                  description_lines.append(f"Outer Cartoons: {rec.outer_id.name}")

         elif rec.packing_type == "pouch":
               if rec.name_id:
                  description_lines.append(f"Name: {rec.name_id.name}")

               if rec.box_cap_id:
                  cap = rec.box_cap_id
                  description_lines.append(
                     f"Capacity per Pouch: {cap.weight} Net {cap.uom_id.name} per Pouch"
                  )

               if rec.branding_id:
                  description_lines.append(f"Branding: {rec.branding_id.name}")

         # Final assignment
         rec.packing_name = "\n".join(description_lines) if description_lines else ""
         rec.is_des = bool(description_lines)