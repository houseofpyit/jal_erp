from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class inheritedProductAttribute(models.Model):
   _inherit = "product.attribute"

   attribute_type = fields.Selection([('grade', 'Grade'),('mesh', 'Mesh'),('bucket', 'Capacity'),
                                      ('pouch_name', 'Pouch Name'),('branding', 'Branding'),('lid_color', 'Lid Color'),
                                      ('drum_color','Drum Color'),('scoops', 'Scoops'),('outer_cartoons', 'Outer Cartoons'),
                                      ('box_color', 'Box Color'),('packing_name', 'Packing Name')], string='Attribute Type')
   default_create = fields.Boolean(string="Default Create")
   active = fields.Boolean(default=True, help="Set active to false to hide the Product Attribute without removing it.")

   def unlink(self):
      for i in self:
         if i.default_create:
               raise ValidationError("Not Allow Delete Record !!!")

      return super(inheritedProductAttribute,self).unlink()

class inheritedProductAttributeValue(models.Model):
   _inherit = "product.attribute.value"

   amount = fields.Float(string="Amount")
   weight = fields.Float(string='Weight')
   uom_id = fields.Many2one('uom.uom',string='Unit')
   packaging_type = fields.Selection([("drum", "Drum"),("bucket", "Bucket"),("box", "Box"),],string="Packaging Type")
   packing_name_ids = fields.Many2many(
      'product.attribute.value',
      'product_attribute_value_packing_rel',  # relation table
      'attribute_value_id',                   # column for current record
      'packing_name_value_id',                # column for related record
      string='Packing Name',
      domain="[('attribute_id.attribute_type','=','packing_name')]")   
   pouch_type = fields.Selection([
      ("bottle", "Bottle"),  
      ("pouch", "Pouch")],string="Pouch Type")
   color = fields.Integer(string='Color')
   packing_type = fields.Selection([
        ("drum", "Drum"), 
        ("bucket", "Bucket"),
        ("usa_bucket", "USA-Bucket"), 
        ("pouch", "Pouch")],string="Packing Type")

   def default_get(self, fields):
      res = super(inheritedProductAttributeValue, self).default_get(fields)
      if self.env.context.get('attribute_type',False):
         product_attribute_rec = self.env['product.attribute'].search([('attribute_type', '=', self.env.context.get('attribute_type',False))],limit=1, order='id')
         res['attribute_id'] = product_attribute_rec.id if product_attribute_rec else False
      return res
   
   @api.onchange('weight', 'uom_id')
   def _onchange_name(self):
      for record in self:
         if record.attribute_id.attribute_type == 'bucket':
            name_parts = []
            if record.weight:
                  name_parts.append(str(record.weight))
            if record.uom_id:
                  name_parts.append(record.uom_id.name)

            record.name = " ".join(name_parts) if name_parts else False

   # def name_get(self):
   #    """Override because in general the name of the value is confusing if it
   #    is displayed without the name of the corresponding attribute.
   #    Eg. on product list & kanban views, on BOM form view

   #    However during variant set up (on the product template form) the name of
   #    the attribute is already on each line so there is no need to repeat it
   #    on every value.
   #    """
   #    print("---------------self._context--------",self._context)
   #    if not self._context.get('show_attribute', True):
   #       return super(inheritedProductAttributeValue, self).name_get()
   #    return [(value.id, "%s: %s" % (value.attribute_id.name, value.name)) for value in self]