from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class inheritedProductTemplate(models.Model):
   _inherit = "product.template"
   
   is_raw_material = fields.Boolean('Raw Material')
   is_finished_goods = fields.Boolean('Finished Goods')
   quality_para_ids = fields.One2many('tempalte.quality.parameter','template_id',string="Quality Parameter")
   is_quality_required = fields.Boolean('Quality Required or Not')
   is_spares = fields.Boolean('Spares')
   bucket_qty_hand_total = fields.Float(
      string="On Hand (Bucket/Bags/Pouch)",
      digits='Product Unit of Measure',
      compute='_compute_template_bucket_qty',
      help="Sum of variant on-hand (Bucket/Bags/Pouch) for this template.",)
   uom_handling_type = fields.Selection([
        ('single', 'Single Unit Handling'),
        ('multi', 'Multi Unit Handling'),
    ], string="UOM Handling Type",default='single')

   def _compute_template_bucket_qty(self):
      for tmpl in self:
         tmpl.bucket_qty_hand_total = sum(tmpl.product_variant_ids.mapped('bucket_qty_hand_total'))

   def action_view_bucket_on_hand(self):
      """Smart button action to open related stock quants."""
      self.ensure_one()
      return {
         'name': 'On Hand (Bucket/Bags/Pouch)',
         'type': 'ir.actions.act_window',
         'res_model': 'stock.quant',
         'view_mode': 'tree,form',
         'views': [(self.env.ref('stock.view_stock_quant_tree_inventory_editable').id, 'tree')],
         'domain': [
               ('product_id', '=', self.id),
               ('location_id.usage', '=', 'internal')
         ],
         'context': {'default_product_id': self.id},
         'target': 'current',
      }

   def action_view_bucket_quants(self):
      self.ensure_one()
      action = self.env.ref('stock.quants').read()[0]
      action['domain'] = [
         ('product_id', 'in', self.product_variant_ids.ids),
         ('location_id.usage', '=', 'internal'),
         ('company_id', '=', self.env.company.id),
      ]
      action.setdefault('context', {})
      return action

   @api.onchange('is_raw_material')
   def _onchange_is_raw_material(self):
      if self.is_raw_material:
         self.is_finished_goods = False
         self.is_packing = False
         self.is_spares = False

   @api.onchange('is_finished_goods')
   def _onchange_is_finished_goods(self):
      if self.is_finished_goods:
         self.is_raw_material = False
         self.is_packing = False
         self.is_spares = False

   @api.onchange('is_packing')
   def _onchange_is_packing(self):
      if self.is_packing:
         self.is_raw_material = False
         self.is_finished_goods = False
         self.is_spares = False

   @api.onchange('is_spares')
   def _onchange_is_spares(self):
      if self.is_spares:
         self.is_raw_material = False
         self.is_finished_goods = False
         self.is_packing = False

class InheritProductProduct(models.Model):
    _inherit = 'product.product'

    bucket_qty_hand_total = fields.Float(
        string="On Hand (Bucket/Bags/Pouch)",
        digits='Product Unit of Measure',
        compute='_compute_bucket_on_hand_total',
        help="Sum of bucket_on_hand from quants in internal locations (this company).",
    )

    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state')
    @api.depends_context(
        'lot_id', 'owner_id', 'package_id', 'from_date', 'to_date',
        'location', 'warehouse', 'allowed_company_ids'
    )
    def _compute_quantities(self):
        res = super(InheritProductProduct, self)._compute_quantities()

        for product in self:
            quants = self.env['stock.quant'].search([
                ('product_id', '=', product.id),
                ('location_id.usage', '=', 'internal')    
            ])
            product.bucket_qty_hand_total = sum(quants.mapped('on_hand_bucket'))
        
        return res
    

    @api.depends_context('company')
    def _compute_bucket_on_hand_total(self):
        Quant = self.env['stock.quant'].sudo()
        # group by product for efficiency
        dom = [
            ('product_id', 'in', self.ids),
            ('location_id.usage', '=', 'internal'),
            ('company_id', '=', self.env.company.id),
        ]
        groups = Quant.read_group(dom, ['on_hand_bucket:sum'], ['product_id'])
        mapped = {g['product_id'][0]: g['on_hand_bucket'] for g in groups}
        for prod in self:
            prod.bucket_qty_hand_total = mapped.get(prod.id, 0.0)


    def action_view_bucket_on_hand(self):
        """Smart button action to open related stock quants."""
        self.ensure_one()
        return {
            'name': 'On Hand (Bucket/Bags/Pouch)',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.quant',
            'view_mode': 'tree,form',
            'views': [(self.env.ref('stock.view_stock_quant_tree_inventory_editable').id, 'tree')],
            'domain': [
                ('product_id', '=', self.id),
                ('location_id.usage', '=', 'internal')
            ],
            'context': {'default_product_id': self.id},
            'target': 'current',
        }
         
class TemplateQualityParameter(models.Model):
    _name = "tempalte.quality.parameter"
    _description = "Tempalte Quality Parameter"

    template_id = fields.Many2one('product.template',string="template",ondelete='cascade')
    item_attribute = fields.Many2one('jal.product.attribute',string="Product Attribute",required=True)
    required_value = fields.Many2one('quality.value',string="Required Value")
    tollerance_range = fields.Char(string="Tollerance Range")
    remarks = fields.Char(string="Remarks")
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

