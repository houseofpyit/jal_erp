from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date,datetime

class JalQuality(models.Model):
    _name = 'jal.quality'
    _description = 'Quality'
    _inherit = ['mail.thread']
    _order = "id desc"

    # def _get_production_id_domain(self):
    #     domain = []
    #     production_ids = self.env['jal.quality'].sudo().search([]).mapped('production_id').ids
    #     if production_ids:
    #         domain.append(('id', 'not in', production_ids))
    #     return domain
    
    name = fields.Char(copy=False, index=True, default=lambda self: _('New'),tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    date = fields.Date(copy=False,string="Date",default=fields.Date.context_today)
    packing_line_ids = fields.One2many('packing.quality.line', 'mst_id')
    finish_line_ids = fields.One2many('finish.quality.line', 'mst_id')
    production_id = fields.Many2one('jal.production',string="Production",copy=False,tracking=True)
    # ,domain=lambda self: self._get_production_id_domain()
    shift_id = fields.Many2one('shift.mst',string="Shift",tracking=True)
    dryer_id = fields.Many2one('dryer.mst',string="Dryer",tracking=True)
    state = fields.Selection([('draft', 'Draft'),('complete', 'Complete')], default='draft',tracking=True)
    grade_id = fields.Many2one('product.attribute.value',string="Grade",domain="[('attribute_id.attribute_type','=','grade')]",tracking=True)
    mesh_id = fields.Many2one('product.attribute.value',string="Mesh",domain="[('attribute_id.attribute_type','=','mesh')]",tracking=True)
    bucket_id = fields.Many2one('product.attribute.value',string="Bucket",domain="[('attribute_id.attribute_type','=','bucket')]",tracking=True)
    no_of_drum = fields.Integer(string="No of Drum",tracking=True)
    approx_weight = fields.Float(string="Approx Weight",tracking=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product',tracking=True)
    user_id = fields.Many2one('res.users',string="User",default=lambda self: self.env.user.id)
    shift_time_id = fields.Many2one('shift.time.line',string="Shift Time",tracking=True)
    quality_para_ids = fields.One2many('quality.parameter.line','mst_id',string="Quality Parameter Line")
    quality_grade_ids = fields.One2many('quality.grade.line','mst_id',string="Quality Grade Line")

    @api.onchange('production_id', 'date')
    def _onchange_shift_time_id(self):
        self.shift_time_id = False
        if not self.production_id or not self.date:
            return {'domain': {'shift_time_id': []}}

        quality_recs = self.env['jal.quality'].search([('production_id', '=', self.production_id.id),('date', '=', self.date)])

        shift_ids = quality_recs.mapped('shift_time_id.id')

        return {'domain': {'shift_time_id': [('id', 'not in', shift_ids)]}}


    @api.onchange('production_id')
    def _onchange_production_id(self):
        self.shift_id = self.production_id.shift_id.id
        self.product_tmpl_id = self.production_id.product_tmpl_id.id

    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        line_list = []
        for line in self.product_tmpl_id.quality_para_ids:
            line_list.append((0,0,{
               'item_attribute': line.item_attribute.id,
               'required_value':line.required_value.id,
               'parameter_remarks':line.remarks,
            }))

        self.quality_para_ids = [(5, 0, 0)] + line_list

        
    def action_complete_btn(self):
        self.state = 'complete'

    @api.model
    def create(self, vals):
        result = super(JalQuality, self).create(vals)
        if vals.get('name', _('New')) == _('New'):
            result['name'] = self.env['ir.sequence'].next_by_code('jal.quality.seq') or _('New')
        
        return result
    
    def get_barcode_data(self):
        line_list = []
        for line in self.quality_grade_ids:
            for _ in range(line.no_of_drum):
                line_list.append({
                    'product_name': self.product_tmpl_id.name,
                    'production_name': self.production_id.name,
                    'name': self.name,
                    'grade_name': line.grade_id.name,
                    'mesh_name': line.mesh_id.name,
                    'dryer_name': self.dryer_id.name,
                    # 'bucket_name': line.bucket_id.name,
                })

        return line_list

class PackingQualityLine(models.Model):
    _name = 'packing.quality.line'
    _description = "Packing Quality Line"

    mst_id = fields.Many2one('jal.quality',string="Mst",ondelete='cascade')

    product_id = fields.Many2one('product.product',required=True)
    uom_id = fields.Many2one('uom.uom',string="Unit")
    qty = fields.Float(string = "Quantity",digits='BaseAmount')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)


    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.uom_id = rec.product_id.uom_po_id.id

class FinishQualityLine(models.Model):
    _name = 'finish.quality.line'
    _description = "Finish Quality Line"

    mst_id = fields.Many2one('jal.quality',string="Mst",ondelete='cascade')
    
    product_id = fields.Many2one('product.product',required=True)
    uom_id = fields.Many2one('uom.uom',string="Unit")
    qty = fields.Float(string = "Quantity",digits='BaseAmount')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.uom_id = rec.product_id.uom_po_id.id


class QualityParameterLine(models.Model):
    _name = "quality.parameter.line"
    _description = "Tempalte Quality Parameter"

    mst_id = fields.Many2one('jal.quality',string="Mst",ondelete='cascade')
    item_attribute = fields.Many2one('jal.product.attribute',string="Product Attribute",required=True)
    required_value = fields.Many2one('quality.value',string="Required Value")
    tollerance_range = fields.Char(string="Tollerance Range")
    parameter_remarks = fields.Char(string="Parameter Remarks")
    remarks = fields.Char(string="Remarks")
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    result_value = fields.Float(string="Result Value")
    is_mg_app = fields.Boolean(string="Manager Approve?")

class QualityGradeLine(models.Model):
    _name = "quality.grade.line"
    _description = "Quality Grade Parameter"

    mst_id = fields.Many2one('jal.quality',string="Mst",ondelete='cascade') 

    grade_id = fields.Many2one('product.attribute.value',string="Grade",domain="[('attribute_id.attribute_type','=','grade')]")
    mesh_id = fields.Many2one('product.attribute.value',string="Mesh",domain="[('attribute_id.attribute_type','=','mesh')]")
    bucket_id = fields.Many2one('product.attribute.value',string="Bucket",domain="[('attribute_id.attribute_type','=','bucket')]")
    no_of_drum = fields.Integer(string="No of Drum")
    weight = fields.Float(string="Weight")
    product_id = fields.Many2one('product.product')
    product_tmpl_id = fields.Many2one('product.template', string='Product Template')
    uom_id = fields.Many2one('uom.uom',string="Unit")

    @api.onchange('product_id','no_of_drum')
    def onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.uom_id = rec.product_id.uom_po_id.id

                rec.weight = rec.no_of_drum * rec.product_id.drum_cap_id.weight

    @api.onchange('grade_id', 'mesh_id', 'bucket_id')
    def _onchange_product_attributes(self):
        if not (self.grade_id and self.mesh_id):
            self.product_id = False
            return {'domain': {'product_id': []}}
        domain = [
            ('product_template_attribute_value_ids.product_attribute_value_id', '=', self.grade_id.id),
            ('product_template_attribute_value_ids.product_attribute_value_id', '=', self.mesh_id.id),
            # ('product_template_attribute_value_ids.product_attribute_value_id', '=', self.bucket_id.id),
            ('product_tmpl_id', '=', self.product_tmpl_id.id)
        ]

        products = self.env['product.product'].search(domain)

        if products:
            self.product_id = products[0].id
            return {'domain': {'product_id': [('id', 'in', products.ids)]}}
        else:
            self.product_id = False
            all_products = self.env['product.product'].search([])
            return {'domain': {'product_id': [('id', 'in', all_products.ids)]}}