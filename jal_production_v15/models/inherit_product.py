from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class inheritedProductTemplate(models.Model):
   _inherit = "product.template"
   
   is_raw_material = fields.Boolean('Raw Material')
   is_finished_goods = fields.Boolean('Finished Goods')
   quality_para_ids = fields.One2many('tempalte.quality.parameter','template_id',string="Quality Parameter")
   is_quality_required = fields.Boolean('Quality Required or Not')
   is_spares = fields.Boolean('Spares')

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
         
class TemplateQualityParameter(models.Model):
    _name = "tempalte.quality.parameter"
    _description = "Tempalte Quality Parameter"

    template_id = fields.Many2one('product.template',string="template",ondelete='cascade')
    item_attribute = fields.Many2one('jal.product.attribute',string="Product Attribute",required=True)
    required_value = fields.Many2one('quality.value',string="Required Value")
    tollerance_range = fields.Char(string="Tollerance Range")
    remarks = fields.Char(string="Remarks")
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

