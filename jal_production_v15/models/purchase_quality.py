from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date,datetime

class JalPurchaseQuality(models.Model):
    _name = 'jal.purchase.quality'
    _description = 'Purchase Quality'
    _inherit = ['mail.thread']
    _order = "id desc"

    
    name = fields.Char(copy=False, index=True, default=lambda self: _('New'),tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    date = fields.Date(copy=False,string="Date",default=fields.Date.context_today,tracking=True)
    send_date = fields.Date(copy=False,string="Send Date")
    purchase_id = fields.Many2one('purchase.order',string="Purchase Order",copy=False)
    picking_id = fields.Many2one('stock.picking',string="Stock Picking",copy=False)
    stage = fields.Selection([('draft', 'Draft'),('pass', 'Pass'),('fail', 'Fail')], default='draft',tracking=True)
    product_id = fields.Many2one('product.product', string='Product',tracking=True)
    qty = fields.Float(string="Quantity",tracking=True,digits='BaseAmount')
    uom_id = fields.Many2one('uom.uom',string="UOM",tracking=True)
    user_id = fields.Many2one('res.users',string="User",default=lambda self: self.env.user.id)
    line_ids = fields.One2many('jal.purchase.quality.line', 'mst_id')

    def action_approve_button(self):
        for line in self.line_ids:
            if line.result_value == 0 and not line.remarks:
                raise ValidationError("Result Value Required !!!")
            
        stock_rec = self.env['stock.move'].search([('picking_id','=',self.picking_id.id),('product_id','=',self.product_id.id)])
        if stock_rec:
            stock_rec.write({'quality_result':'pass'})

        self.stage = 'pass'

    def action_reject_button(self):
        for line in self.line_ids:
            if line.result_value == 0 and not line.remarks:
                raise ValidationError("Result Value Required !!!")
            
        stock_rec = self.env['stock.move'].search([('picking_id','=',self.picking_id.id),('product_id','=',self.product_id.id)])
        if stock_rec:
            stock_rec.write({'quality_result':'fail'})

        self.stage = 'fail'


    # @api.onchange('production_id')
    # def _onchange_production_id(self):
    #     self.shift_id = self.production_id.shift_id.id
    #     self.product_tmpl_id = self.production_id.product_tmpl_id.id

    # @api.onchange('product_tmpl_id')
    # def _onchange_product_tmpl_id(self):
    #     line_list = []
    #     for line in self.product_tmpl_id.quality_para_ids:
    #         line_list.append((0,0,{
    #            'item_attribute': line.item_attribute.id,
    #            'required_value':line.required_value.id,
    #            'parameter_remarks':line.remarks,
    #         }))

    #     self.quality_para_ids = [(5, 0, 0)] + line_list

    @api.model
    def create(self, vals):
        result = super(JalPurchaseQuality, self).create(vals)
        if vals.get('name', _('New')) == _('New'):
            result['name'] = self.env['ir.sequence'].next_by_code('purchase.quality.seq') or _('New')
        
        return result
    
    # def get_barcode_data(self):
    #     line_list = []
    #     for line in self.quality_grade_ids:
    #         for _ in range(line.no_of_drum):
    #             line_list.append({
    #                 'product_name': self.product_tmpl_id.name,
    #                 'production_name': self.production_id.name,
    #                 'name': self.name,
    #                 'grade_name': line.grade_id.name,
    #                 'mesh_name': line.mesh_id.name,
    #                 'dryer_name': self.dryer_id.name,
    #                 'bucket_name': line.bucket_id.name,
    #             })

    #     return line_list

class JalPurchaseQualityLine(models.Model):
    _name = "jal.purchase.quality.line"
    _description = "Tempalte Quality Parameter"

    mst_id = fields.Many2one('jal.purchase.quality',string="Mst",ondelete='cascade')
    item_attribute = fields.Many2one('jal.product.attribute',string="Product Attribute",required=True)
    required_value = fields.Many2one('quality.value',string="Required Value")
    parameter_remarks = fields.Char(string="Parameter Remarks")
    remarks = fields.Char(string="Remarks")
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    result_value = fields.Float(string="Result Value")
