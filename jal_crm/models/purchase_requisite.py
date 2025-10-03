from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date,datetime

class JalPurchaseRequisite(models.Model):
    _name = 'jal.purchase.requisite'
    _description = 'Purchase Requisite'
    _inherit = ['mail.thread']
    _order = "id desc"


    name = fields.Char(copy=False, index=True, default=lambda self: _('New'))
    user_id = fields.Many2one('res.users',string="User")
    sale_id = fields.Many2one('sale.order',string="Sale No.")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    date_order = fields.Date(copy=False,string="Requisition Date",default=fields.Date.context_today)
    date_confirm = fields.Date(copy=False,string="Confirm Date" )
    line_ids = fields.One2many('jal.purchase.requisite.line', 'mst_id')
    state = fields.Selection([('draft', 'Draft'),('confirm', 'Confirm')], default='draft')
    is_po_count = fields.Integer(string="PO Count", compute="_compute_po_count", store=True)

    # @api.depends('is_po_count') 
    # def _compute_po_count(self):
    #     print("----------------cccccccccccccccccccccccccccc-")
    #     for i in self:
    #         print("-------_compute_po called-------")
    #         po_count = self.env['purchase.order'].sudo().search_count([('pur_req_id', '=', i.id)])
    #         i.is_po_count = po_count

    #         if po_count > 0:
    #             i.date_confirm = fields.Datetime.now()
    #             i.state = 'confirm'
    #         else:
    #             i.date_confirm = False
    #             i.state = 'draft'

    def action_view_pur_order(self):
      pur_rec = self.env['purchase.order'].search([('pur_req_id', '=', self.id)])
      return {
         'type': 'ir.actions.act_window',
         'name': 'Requests for Quotation',
         'view_mode': 'form',
         'res_model': 'purchase.order',
         'res_id': pur_rec.id,
         'context': {'create': False}
         }

    def create_purchase_po(self):
         line_list = []
         for line in self.line_ids:
            line_list.append((0,0,{
               'product_id': line.product_id.id,
               'product_qty':line.qty,
               'product_uom':line.uom_id.id,
               'date_planned': fields.Datetime.now(),
               'hsn_id':line.product_id.hsn_id.id,
               'price_unit': line.product_id.standard_price,
               'name': (f"{line.product_id.description_purchase}" if line.product_id.description_purchase else f"{line.product_id.display_name}"),
            }))
         return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'view_mode': 'form',
            'res_model': 'purchase.order', 
            'context': {'default_pur_req_id': self.id,'default_order_line':line_list},
            'target': 'current', 
         }

    @api.model
    def create(self, vals):
        result = super(JalPurchaseRequisite, self).create(vals)
        if vals.get('name', _('New')) == _('New'):
            result['name'] = self.env['ir.sequence'].next_by_code('jal.purchase.requisite.seq') or _('New')
        
        return result
    
    # def unlink(self):
    #     for i in self:
    #         if i.state in ['approve','reject']:
    #             raise ValidationError("Not Allow Delete Create RFQ / Cancel Record !!!")

    #     return super(AJPurchaseRequisite,self).unlink()

    # def button_approved(self):
    #     self.state = "approved"

    # def button_approve(self):
    #     # for line in self.pr_line_ids:
    #         # if not line.vendor_ids:
    #         #     raise ValidationError("Please select vendor in product line !!!")

    #     self.date_approve = date.today()
    #     for l in self.pr_line_ids.mapped('vendor_ids'):
    #         for v in set(self.pr_line_ids.mapped('voucher_type')):
    #             line_list = []
    #             rec = self.env['aj.purchase.requisite'].search([('id','=',self.id)])
    #             for i in rec.pr_line_ids:
    #                 if l.id in i.vendor_ids.ids and v == i.voucher_type:
    #                     if i.pen_po_qty > 0:
    #                         line_list.append((0,0,{
    #                             'product_id': i.product_id.id,
    #                             'name':i.product_id.name,
    #                             'product_uom': i.uom_id.id,
    #                             'product_qty': i.pen_po_qty,
    #                             'req_dt' : i.req_dt,
    #                             'hsn_id':i.product_id.hsn_id.id,
    #                             'price_unit': i.product_id.standard_price,
    #                             'pr_line_id' : i.id,
    #                         }))
    #             serial = 0
    #             # if self.state == "draft":
    #             qt_order_chr = self.env.company.prefix +"/QT/"+ self.env.user.fy_from_date.strftime("%y") + "-" + self.env.user.fy_to_date.strftime("%y") + "/"
    #             query = ''' Select max(qt_order_no) From purchase_order Where company_id = ''' + str(self.env.company.id)+ " and qt_order_chr = '" + str(qt_order_chr) +"'"
    #             if self.env.user.fy_year_id:
    #                 query += " and date >=  " +"'" + str(self.env.user.fy_from_date) +"'"
    #                 query += " and date <=  " +"'" + str(self.env.user.fy_to_date) +"'"

    #             self.env.cr.execute(query)
    #             query_result = self.env.cr.dictfetchall()
    #             serial = False
    #             if query_result[0]['max'] == None :
    #                 serial = 1
    #             else:
    #                 serial = 1 + query_result[0]['max']
    #             if line_list:
    #                 po = self.env['purchase.order'].sudo().create({
    #                     'qt_order_chr': qt_order_chr,
    #                     'qt_order_no': serial,
    #                     'partner_id': l.id,
    #                     'pr_id': self.id,
    #                     'voucher_type':v,
    #                     'company_id': self.env.company.id,
    #                     'order_line': line_list,
    #                 })
    #                 po._onchange_partner_id()
    #                 po._onchange_voucher_type()
    #                 # po._onchange_qt_order_chr()
    #                 # po._onchange_order_chr()
    #                 # po.order_chr_vld()
    #                 # po._onchange_chr_no()
    #                 for line in po.order_line:
    #                     line._onchange_hsn_id()
    #                     line._onchange_calc_amt()
    #     view = self.env.ref('purchase.purchase_order_form')
    #     tree = self.env.ref('purchase.purchase_order_kpis_tree')

    #     self.state = "approve"
    #     return {
    #         'name' : 'Requests for Quotation',
    #         'type' : 'ir.actions.act_window',
    #         'view_mode' : 'tree,form',
    #         'views': [(tree.id,'list'),(view.id, 'form')],
    #         'res_model' : 'purchase.order',
    #         'target' : 'current',
    #         'domain' : [('pr_id', '=', self.id)],
    #         'context': "{'create': 0}"
    #     }


    # def button_reject(self):
    #     self.state = "reject"

class JalPurchaseRequisiteLine(models.Model):
    _name = 'jal.purchase.requisite.line'
    _description = "Purchase Requisite Line"

    mst_id = fields.Many2one('jal.purchase.requisite',string="Purchase Req",ondelete='cascade')
    product_id = fields.Many2one('product.product',required=True)
    uom_id = fields.Many2one('uom.uom',string="Unit")
    qty = fields.Float(string = "Quantity",digits='BaseAmount')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    # def _compute_pen_po_qty(self):
    #     for i in self:
    #         i.is_compute = True
    #         i.po_qty = sum(self.env['purchase.order.line'].search([('pr_line_id','=',i.id),('order_id.state','=','purchase')]).mapped('product_qty'))
    #         i.pen_po_qty = i.qty - sum(self.env['purchase.order.line'].search([('pr_line_id','=',i.id),('order_id.state','=','purchase')]).mapped('product_qty'))
    #         i.purchase_requisite_id._onchange_pr_line_ids()

    # @api.onchange('product_id')
    # def onchange_product_id(self):
    #     for rec in self:
    #         if rec.product_id:
    #             rec.uom_id = rec.product_id.uom_po_id.id
    #             # if rec.product_id.is_raw_material == True:
    #             #     rec.voucher_type = "raw"
    #             # if rec.product_id.is_packing == True:
    #             #     rec.voucher_type = "packing"
    #             # if rec.product_id.is_trade == True:
    #             #     rec.voucher_type = "trade_item"
    #             # if rec.product_id.is_spare == True:
    #             #     rec.voucher_type = "engineering"
    #         rec.cur_stock = rec.product_id.qty_available

    # @api.model
    # def create(self, vals):
    #     if not vals.get('qty'):
    #         raise ValidationError("Quantity Must Be Greater Than Zero !!!!")
    #     result = super(AJPurchaseRequisiteLine, self).create(vals)
        
    #     return result
    
    # def unlink(self):
    #     for req in self.purchase_requisite_id:
    #         if req.state in ['request','approved','approve','reject']:
    #             raise ValidationError('You cannot delete!!!')
    #     return super(AJPurchaseRequisiteLine, self).unlink()
                