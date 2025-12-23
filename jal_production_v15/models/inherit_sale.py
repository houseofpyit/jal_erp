from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class InheritSale(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(InheritSale, self).action_confirm()
        for line in self.order_line:
            stock_move = self.env['stock.move'].search([('sale_line_id', '=', line.id)])
            stock_move.write({'demand_bucket': line.bucket})
        return res
    
class inheritedSaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    grade_id = fields.Many2one('product.attribute.value',string="Grade",domain="[('attribute_id.attribute_type','=','grade')]")
    mesh_id = fields.Many2one('product.attribute.value',string="Mesh",domain="[('attribute_id.attribute_type','=','mesh')]")
    bucket = fields.Float(string='Packing Unit',store=True)
    uom_handling_type = fields.Selection(related='product_tmpl_id.uom_handling_type',string="UoM Handling Type",store=False)

    drum_cap_id = fields.Many2one('product.attribute.value',string="Capacity Per Drum",domain="[('packaging_type','=','drum'),('attribute_id.attribute_type','=','bucket')]")
    bucket_cap_id = fields.Many2one('product.attribute.value',string="Capacity",domain="[('attribute_id.attribute_type','=','bucket'),('packing_name_ids','in', name_id)]")
    box_cap_id = fields.Many2one('product.attribute.value',string="Capacity Per Box",domain="[('packaging_type','=','box'),('attribute_id.attribute_type','=','bucket')]")
    pouch_id = fields.Many2one('product.attribute.value',string="Pouch Name",domain="[('attribute_id.attribute_type','=','pouch_name')]")
    name_id = fields.Many2one('product.attribute.value',string="Name",domain="[('attribute_id.attribute_type','=','packing_name')]")
    lid_id = fields.Many2one('product.attribute.value',string="Lid Color",domain="[('attribute_id.attribute_type','=','lid_color')]")
    # branding_id = fields.Many2one('product.attribute.value',string="Branding",domain="[('attribute_id.attribute_type','=','branding')]")
    box_id = fields.Many2one('product.attribute.value',string="Box Color",domain="[('attribute_id.attribute_type','=','box_color')]")
    drum_color_id = fields.Many2one('product.attribute.value',string="Drum Color",domain="[('attribute_id.attribute_type','=','drum_color')]")
    scoops_id = fields.Many2one('product.attribute.value',string="Scoops",domain="[('attribute_id.attribute_type','=','scoops')]")
    outer_id = fields.Many2one('product.attribute.value',string="Outer Cartoons",domain="[('attribute_id.attribute_type','=','outer_cartoons')]")

    branding_id = fields.Many2one('branding.mst',string="Branding")
    packing_name = fields.Html(
        string="Packing Description",
        compute="_compute_packing_name",
        store=True,
        sanitize=False,   # optional: set True if you want Odoo to sanitize HTML
    )
    is_des = fields.Boolean(string="Has Description", compute="_compute_packing_name", store=True)

    @api.onchange('grade_id','mesh_id','product_tmpl_id','lid_id')
    def _onchange_grade_id(self):
        # if not (self.grade_id and self.mesh_id and self.lid_id and self.product_tmpl_id):
        #     self.product_id = False
        #     return {'domain': {'product_id': []}}
        domain = [
            ('product_tmpl_id', '=', self.product_tmpl_id.id)
        ]
        if self.grade_id:
            domain.append(('product_template_attribute_value_ids.product_attribute_value_id', '=', self.grade_id.id))
        if self.mesh_id:
            domain.append(('product_template_attribute_value_ids.product_attribute_value_id', '=', self.mesh_id.id))
        if self.lid_id:
            domain.append(('product_template_attribute_value_ids.product_attribute_value_id', '=', self.lid_id.id))
            
        products = self.env['product.product'].search(domain)

        if products:
            self.product_id = products[0].id
            return {'domain': {'product_id': [('id', 'in', products.ids)]}}
        else:
            self.product_id = False
            all_products = self.env['product.product'].search([])
            return {'domain': {'product_id': [('id', 'in', all_products.ids)]}}
        

    @api.onchange('product_tmpl_id','product_uom_qty','product_uom')
    def _onchange_bucket_cap_id(self):
        for rec in self:
            if rec.product_tmpl_id.drum_cap_id.weight > 0:
                rec.bucket = (rec.product_uom_qty * rec.product_uom.ratio) / rec.product_tmpl_id.drum_cap_id.weight
            else:
                rec.bucket = 0

    @api.onchange('name_id')
    def _onchange_name_id(self):
        self.bucket_cap_id = False

    @api.onchange('packing_type')
    def _onchange_packing_type(self):
        self.drum_cap_id = False
        self.bucket_cap_id = False
        self.box_cap_id = False
        self.pouch_id = False
        self.name_id = False
        self.lid_id = False
        self.branding_id = False
        self.box_id = False
        self.drum_color_id = False
        self.scoops_id = False
        self.outer_id = False

            
    @api.depends(
        'product_tmpl_id','packing_type', 'name_id', 'drum_cap_id', 'bucket_cap_id', 'box_cap_id',
        'branding_id', 'lid_id', 'drum_color_id', 'box_id', 'pouch_id',
        'scoops_id', 'outer_id', 'pouch_type'
    )
    def _compute_packing_name(self):
        for rec in self:
            desc = ""  # Final HTML string

            # if rec.packing_type == "drum":
            #     desc += "<b>Drum Packing</b><ul>"
                
            #     if rec.name_id:
            #         desc += f"<li>Name: {rec.name_id.name}</li>"

            #     if rec.bucket_cap_id:
            #         cap = rec.bucket_cap_id
            #         desc += f"<li>Capacity per Drum: {cap.weight} {cap.uom_id.name} Net per Drum</li>"

            #     if rec.branding_id:
            #         desc += f"<li>Branding: {rec.branding_id.name}</li>"

            #     if rec.lid_id:
            #         desc += f"<li>Lid Colour: {rec.lid_id.name}</li>"

            #     if rec.drum_color_id:
            #         desc += f"<li>Drum Colour: {rec.drum_color_id.name}</li>"

            #     desc += "</ul>"

            # elif rec.packing_type == "bucket":
            #     desc += "<b>Bucket Packing</b><ul>"

            #     if rec.name_id:
            #         desc += f"<li>Name: {rec.name_id.name}</li>"

            #     if rec.bucket_cap_id:
            #         cap = rec.bucket_cap_id
            #         desc += f"<li>Capacity per Bucket: {cap.weight} {cap.uom_id.name} Net per Bucket</li>"

            #     if rec.branding_id:
            #         desc += f"<li>Branding: {rec.branding_id.name}</li>"

            #     if rec.lid_id:
            #         desc += f"<li>Lid Colour: {rec.lid_id.name}</li>"

            #     if rec.drum_color_id:
            #         desc += f"<li>Drum Colour: {rec.drum_color_id.name}</li>"

            #     desc += "</ul>"

            # elif rec.packing_type == "usa_bucket":
            #     desc += "<b>USA Bucket Packing</b><ul>"

            #     if rec.name_id:
            #         desc += f"<li>Name: {rec.name_id.name}</li>"

            #     if rec.bucket_cap_id:
            #         cap = rec.bucket_cap_id
            #         desc += f"<li>Capacity per USA Bucket: {cap.weight} {cap.uom_id.name} Net per USA Bucket</li>"

            #     if rec.branding_id:
            #         desc += f"<li>Branding: {rec.branding_id.name}</li>"

            #     if rec.lid_id:
            #         desc += f"<li>Lid Colour: {rec.lid_id.name}</li>"

            #     if rec.drum_color_id:
            #         desc += f"<li>Drum Colour: {rec.drum_color_id.name}</li>"

            #     if rec.scoops_id:
            #         desc += f"<li>Scoops: {rec.scoops_id.name}</li>"

            #     if rec.outer_id:
            #         desc += f"<li>Outer Cartoons: {rec.outer_id.name}</li>"

            #     desc += "</ul>"

            # elif rec.packing_type == "pouch":
            #     desc += "<b>Pouch Packing</b><ul>"

            #     if rec.name_id:
            #         desc += f"<li>Name: {rec.name_id.name}</li>"

            #     if rec.bucket_cap_id:
            #         cap = rec.bucket_cap_id
            #         desc += f"<li>Capacity per Pouch: {cap.weight} {cap.uom_id.name} Net per Pouch</li>"

            #     if rec.pouch_type:
            #         desc += f"<li>Pouch Type: {rec.pouch_type}</li>"

            #     if rec.pouch_id:
            #         desc += f"<li>Pouch Name: {rec.pouch_id.name}</li>"

            #     if rec.box_id:
            #         desc += f"<li>Box Colour: {rec.box_id.name}</li>"
                    

            #     if rec.branding_id:
            #         desc += f"<li>Branding: {rec.branding_id.name}</li>"

            #     desc += "</ul>"

            if rec.product_tmpl_id:
                desc += f"<li>Name : {rec.product_tmpl_id.name}</li>"

            if rec.branding_id:
                desc += f"<li>Branding : {rec.branding_id.name}</li>"

            if rec.lid_id:
                desc += f"<li>Lid Color : {rec.lid_id.name}</li>"

            rec.packing_name = desc or "NEW"
            rec.is_des = bool(desc)

    