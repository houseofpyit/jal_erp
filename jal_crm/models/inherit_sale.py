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
   
   business_type = fields.Selection([("international", "International"), ("domestic", "Domestic"), ("trading", "Trading")],string="Business Type",tracking=True,default=lambda self: self.env.context.get('default_business_type',False))
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
                                            ('sale', 'Confirm PI'),
                                            ('close_order','Close Order')],tracking=True)
   po_no = fields.Char(string="PO",tracking=True)
   po_date = fields.Date(string="PO Date",tracking=True)
   reference = fields.Char(string="Reference",tracking=True)
   freight = fields.Float(string="Total Freight (Amount)",tracking=True)
   insurance = fields.Float(string="Total Insurance (Amount)",tracking=True)
   fob_rates = fields.Float(string="FOB Rates (Amount)",tracking=True)
   inspection = fields.Selection([
        ("yes", "Yes"),  
        ("no", "No")],string="Pre-Shipment Inspection",tracking=True)
   lading_type = fields.Selection([('house_bl','House BL'),
                              ('master_bl','Master BL')],string="Bill of Lading Type",tracking=True)
   purchase_req_count = fields.Integer(string="Purchase Requisition Count", copy=False)
   display_name_on_pi = fields.Selection([
        ("product_name", "Product Name"),  
        ("shipping_name", "Shipping Name")],default="product_name",string="Display Name On PI",tracking=True)
   buyer_notify_id = fields.Many2one('res.partner',string="Buyer & Notify",tracking=True)
   buyer_ref_details = fields.Text(string="Buyer Reference Details",tracking=True)
   jal_currency_id = fields.Many2one('res.currency',string="Currency")
   shipping_id = fields.Many2one('product.shipping.mst',string="Shipping Name")
   product_shipping_id = fields.Many2one('product.shipping.mst',string="Product Name")
   product_expiry = fields.Selection([
      ('1', '1 Year'),
      ('2', '2 Years'),
      ('3', '3 Years'),
      ('4', '4 Years'),
      ('5', '5 Years'),
   ], string="Product Expiry")

   acc_user_id = fields.Many2one('res.users',string="Account User",tracking=True)
   dis_user_id = fields.Many2one('res.users',string="Dispatch User",tracking=True)
   team_user_id = fields.Many2one('res.users',string="Saleteam User",tracking=True)

   acc_date = fields.Datetime(string="Date",tracking=True)
   dis_date = fields.Datetime(string="Date",tracking=True)
   team_date = fields.Datetime(string="Date",tracking=True)

   acc_comment = fields.Text(string="Comment",tracking=True)
   dis_comment = fields.Text(string="Comment",tracking=True)
   team_comment = fields.Text(string="Comment",tracking=True)

   # @api.onchange('team_id')
   # def _onchange_team_id(self):
   #    self.business_type = self.team_id.business_type

   @api.onchange('jal_currency_id')
   @api.depends('jal_currency_id')
   def _onchange_jal_currency_id(self):
      if self.jal_currency_id:
         self.currency_id = self.jal_currency_id.id

   def default_get(self, fields):
      res = super(inheritedSaleOrder, self).default_get(fields)
      if self.env.context.get('default_business_type',False) == 'international':
         res['currency_id'] = self.env.ref('base.USD').id
         res['jal_currency_id'] = self.env.ref('base.USD').id
      else:
         res['currency_id'] = self.env.company.currency_id.id
      return res
   
   def amount_to_text(self, amount, currency):
      if currency == 'INR':
         words = num2words(amount, lang='en_IN')
         suffix = ' Rupees'
      else:
         words = num2words(amount, lang='en')
         suffix = ''
      words = words.replace(",", " ").title()
      return f"{words}{suffix}"
   
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

   def action_acc_aprove(self):
      return {
         'type': 'ir.actions.act_window',
         'name': 'Account Approve',
         'view_mode': 'form',
         'res_model': 'sale.aprove.wiz',
         'target': 'new',
         'context': {'default_aprove_type': 'account'},
         }

   def action_dis_aprove(self):
      return {
         'type': 'ir.actions.act_window',
         'name': 'Dispatch Approve',
         'view_mode': 'form',
         'res_model': 'sale.aprove.wiz',
         'target': 'new',
         'context': {'default_aprove_type': 'dispatch'},
         }

   def action_team_aprove(self):
      return {
         'type': 'ir.actions.act_window',
         'name': 'Saleteam Approve',
         'view_mode': 'form',
         'res_model': 'sale.aprove.wiz',
         'target': 'new',
         'context': {'default_aprove_type': 'saleteam'},
         }

   def action_quotation_confirm(self):
      self.state = 'quotation_confirm'

   def action_create_pi(self):
      self.action_confirm()
      self.state = 'create_pi'

   @api.model
   def create(self, vals):
      if vals.get('jal_currency_id'):
         vals['currency_id'] = vals['jal_currency_id']
      res = super(inheritedSaleOrder, self).create(vals)
      if res.jal_currency_id:
         res.currency_id = res.jal_currency_id.id
      return res
   
   def write(self, vals):
      if vals.get('jal_currency_id'):
         vals['currency_id'] = vals['jal_currency_id']
      res = super(inheritedSaleOrder, self).write(vals)

      return res

class inheritedSaleOrderLine(models.Model):
   _inherit = "sale.order.line"

   shipping_id = fields.Many2one('product.shipping.mst',string="Shipping Name")
   product_shipping_id = fields.Many2one('product.shipping.mst',string="Product Name")
   # drum_cap_id = fields.Many2one('capacity.mst',string="Capacity Per Drum",domain="[('packaging_type','=','drum')]")
   # bucket_cap_id = fields.Many2one('capacity.mst',string="Capacity",domain="[('packaging_type','=','bucket')]")
   # box_cap_id = fields.Many2one('capacity.mst',string="Capacity Per Box",domain="[('packaging_type','=','box')]")
   # pouch_id = fields.Many2one('pouch.name.mst',string="Pouch Name")
   # name_id = fields.Many2one('name.mst',string="Name")
   # lid_id = fields.Many2one('lid.color.mst',string="Lid Color")
   # branding_id = fields.Many2one('branding.mst',string="Branding")
   # box_id = fields.Many2one('box.color.mst',string="Box Color")
   # drum_color_id = fields.Many2one('drum.color.mst',string="Drum Color")
   # scoops_id = fields.Many2one('scoops.mst',string="Scoops")
   # outer_id = fields.Many2one('outer.cartoons.mst',string="Outer Cartoons")
   packing_type = fields.Selection([("drum", "Drum"), ("bucket", "Bucket"),("usa_bucket", "USA-Bucket"), ("pouch", "Pouch")],string="Packing Type")
   packing_name = fields.Html(
      string="Packing Description",
      store=True,
      sanitize=False,   # optional: set True if you want Odoo to sanitize HTML
   )
   is_des = fields.Boolean(string="Has Description", store=True)
   name = fields.Text(string='Description',required=False)
   product_tmpl_id = fields.Many2one('product.template', string='Product Template', domain=[('sale_ok', '=', True)])
   pouch_type = fields.Selection([
      ("pouch", "Pouch"), 
      ("bottle", "Bottle")],string="Pouch Type")
   product_form_type = fields.Selection([
      ("granules", "Granules"), 
      ("tablet", "Tablet")],string="Product Form")
   
   @api.onchange('product_tmpl_id')
   def _onchange_product_tmpl_id(self):
      self.product_uom = self.product_tmpl_id.uom_id.id
      self.price_unit = self.product_tmpl_id.list_price

   def get_sale_order_line_multiline_description_sale(self, product):
      res = super(inheritedSaleOrderLine, self).get_sale_order_line_multiline_description_sale(product)
      return ''

   #  @api.onchange('product_id')
   #  def _onchange_product_id(self):
   #      if self.product_id:
   #          self.hsn_id = self.product_id.hsn_id.id
   #          self.price_unit = self.product_id.list_price
   #          if self.order_id.partner_id.disc:
   #              self.disc_per = self.order_id.partner_id.disc

   # @api.onchange('packing_type')
   # def _onchange_packing_type(self):
   #    self.drum_cap_id = False
   #    self.bucket_cap_id = False
   #    self.box_cap_id = False
   #    self.pouch_id = False
   #    self.name_id = False
   #    self.lid_id = False
   #    self.branding_id = False
   #    self.box_id = False
   #    self.drum_color_id = False
   #    self.scoops_id = False
   #    self.outer_id = False

         
   # @api.depends(
   #  'packing_type', 'name_id', 'drum_cap_id', 'bucket_cap_id', 'box_cap_id',
   #  'branding_id', 'lid_id', 'drum_color_id', 'box_id', 'pouch_id',
   #  'scoops_id', 'outer_id', 'pouch_type'
   # )
   # def _compute_packing_name(self):
   #    for rec in self:
   #       desc = ""  # Final HTML string

   #       if rec.packing_type == "drum":
   #             desc += "<b>Drum Packing</b><ul>"
               
   #             if rec.name_id:
   #                desc += f"<li>Name: {rec.name_id.name}</li>"

   #             if rec.bucket_cap_id:
   #                cap = rec.bucket_cap_id
   #                desc += f"<li>Capacity per Drum: {cap.weight} {cap.uom_id.name} Net per Drum</li>"

   #             if rec.branding_id:
   #                desc += f"<li>Branding: {rec.branding_id.name}</li>"

   #             if rec.lid_id:
   #                desc += f"<li>Lid Colour: {rec.lid_id.name}</li>"

   #             if rec.drum_color_id:
   #                desc += f"<li>Drum Colour: {rec.drum_color_id.name}</li>"

   #             desc += "</ul>"

   #       elif rec.packing_type == "bucket":
   #             desc += "<b>Bucket Packing</b><ul>"

   #             if rec.name_id:
   #                desc += f"<li>Name: {rec.name_id.name}</li>"

   #             if rec.bucket_cap_id:
   #                cap = rec.bucket_cap_id
   #                desc += f"<li>Capacity per Bucket: {cap.weight} {cap.uom_id.name} Net per Bucket</li>"

   #             if rec.branding_id:
   #                desc += f"<li>Branding: {rec.branding_id.name}</li>"

   #             if rec.lid_id:
   #                desc += f"<li>Lid Colour: {rec.lid_id.name}</li>"

   #             if rec.drum_color_id:
   #                desc += f"<li>Drum Colour: {rec.drum_color_id.name}</li>"

   #             desc += "</ul>"

   #       elif rec.packing_type == "usa_bucket":
   #             desc += "<b>USA Bucket Packing</b><ul>"

   #             if rec.name_id:
   #                desc += f"<li>Name: {rec.name_id.name}</li>"

   #             if rec.bucket_cap_id:
   #                cap = rec.bucket_cap_id
   #                desc += f"<li>Capacity per USA Bucket: {cap.weight} {cap.uom_id.name} Net per USA Bucket</li>"

   #             if rec.branding_id:
   #                desc += f"<li>Branding: {rec.branding_id.name}</li>"

   #             if rec.lid_id:
   #                desc += f"<li>Lid Colour: {rec.lid_id.name}</li>"

   #             if rec.drum_color_id:
   #                desc += f"<li>Drum Colour: {rec.drum_color_id.name}</li>"

   #             if rec.scoops_id:
   #                desc += f"<li>Scoops: {rec.scoops_id.name}</li>"

   #             if rec.outer_id:
   #                desc += f"<li>Outer Cartoons: {rec.outer_id.name}</li>"

   #             desc += "</ul>"

   #       elif rec.packing_type == "pouch":
   #             desc += "<b>Pouch Packing</b><ul>"

   #             if rec.name_id:
   #                desc += f"<li>Name: {rec.name_id.name}</li>"

   #             if rec.bucket_cap_id:
   #                cap = rec.bucket_cap_id
   #                desc += f"<li>Capacity per Pouch: {cap.weight} {cap.uom_id.name} Net per Pouch</li>"

   #             if rec.pouch_type:
   #                desc += f"<li>Pouch Type: {rec.pouch_type}</li>"

   #             if rec.pouch_id:
   #                desc += f"<li>Pouch Name: {rec.pouch_id.name}</li>"

   #             if rec.box_id:
   #                desc += f"<li>Box Colour: {rec.box_id.name}</li>"
                  

   #             if rec.branding_id:
   #                desc += f"<li>Branding: {rec.branding_id.name}</li>"

   #             desc += "</ul>"

   #       rec.packing_name = desc or ""
   #       rec.is_des = bool(desc)
