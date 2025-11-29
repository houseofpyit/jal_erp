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
    state = fields.Selection([('draft', 'Draft'),('sent', 'Sent to Manager'),('approved', 'Approved'),('confirm', 'Confirm')], default='draft')
    is_po_count = fields.Integer(string="PO Count", compute="compute_po_count")

    @api.depends('date_confirm','line_ids','state') 
    def compute_po_count(self):
        for i in self:
            po_count = self.env['purchase.order'].sudo().search_count([('pur_req_id', '=', i.id)])
            i.is_po_count = po_count

            if po_count > 0:
                i.date_confirm = fields.Datetime.now()
                i.state = 'confirm'
            else:
                i.date_confirm = False
                if i.state == 'confirm':
                    i.state = 'approved'

    def action_send_manager(self):
        if not self.line_ids:
            raise ValidationError("Add product details before sending.")
        self.state = 'sent'

    def action_approved(self):
        self.state = 'approved'

    def action_view_pur_order(self):
      pur_rec = self.env['purchase.order'].search([('pur_req_id', '=', self.id)])
      if len(pur_rec) == 1: 
        return {
            'type': 'ir.actions.act_window',
            'name': 'Requests for Quotation',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'res_id': pur_rec.id,
            'context': {'create': False}
            }
      else:        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Requests for Quotation',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', pur_rec.ids)],
            'context': {'create': False}
            }

    def create_purchase_po(self):
         if not self.line_ids:
            raise ValidationError("Add product details before sending.")
         for line in self.line_ids:
            if not line.product_id:
                raise ValidationError("Some product lines are missing a product. Please complete the details.")
            if not line.qty or line.qty <= 0:
                raise ValidationError("Quantity cannot be zero. Please correct the product details.")
            
         line_list = []
         for line in self.line_ids:
            line_list.append((0,0,{
               'product_id': line.product_id.id,
               'product_qty':line.qty,
               'product_uom':line.uom_id.id,
               'date_planned': fields.Datetime.now(),
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

class JalPurchaseRequisiteLine(models.Model):
    _name = 'jal.purchase.requisite.line'
    _description = "Purchase Requisite Line"

    mst_id = fields.Many2one('jal.purchase.requisite',string="Purchase Req",ondelete='cascade')
    product_id = fields.Many2one('product.product',required=True,domain=[('is_finished_goods','=',False)])
    uom_id = fields.Many2one('uom.uom',string="Unit")
    qty = fields.Float(string = "Quantity",digits='BaseAmount')
    description = fields.Char(string="Description")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_po_id.id

                