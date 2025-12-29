from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class inheritSaleOrder(models.Model):
    _inherit = "sale.order"

    total_mt_amt = fields.Float(string="Total MT Amount")

    @api.depends('order_line')
    def _final_amt_calculate(self):
        res = super(inheritSaleOrder, self)._final_amt_calculate()
        for i in self:
            total_mt_amt = 0
            for line in i.order_line:
                if line.product_uom.factor:
                    total_mt_amt += (line.product_uom_qty / line.product_uom.factor) / 1000
            i.total_mt_amt = total_mt_amt
        return res

    @api.onchange('freight','net_amt','insurance','order_line')
    def _onchange_freight(self):
        for rec in self:
            if rec.freight > 0:
                rec.fob_rates = (rec.net_amt - rec.freight - rec.insurance)
            else:
                rec.fob_rates = 0

    @api.onchange('order_chr','order_no')
    def _onchange_chr_no(self):
        pass

    def action_create_pi(self):
        res = super(inheritSaleOrder, self).action_create_pi()
        self.order_no = self.order_chr_vld()
        if self.order_chr:
            self.name = str(self.order_chr)+ str(self.order_no)
        else:
            self.name = self.order_no

        for pic in self.picking_ids:
            pic.write({'origin': self.name})
        return res

    @api.model
    def create(self, vals):
        res = super(inheritSaleOrder, self).create(vals)
        res.name = 'New'
        res.order_no = None
        return res
    
    def action_advance_receipt(self):
        return {
            'name': 'Advance Receipt',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.advance.receipt.wiz',
            'target':'new',
        }

class inheritSaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    @api.onchange('product_template_id')
    def _onchange_product_template_id(self):
        if self.product_template_id:
            self.hsn_id = self.product_template_id.hsn_id.id
            self.price_unit = self.product_template_id.list_price
            if self.order_id.partner_id.disc:
                self.disc_per = self.order_id.partner_id.disc

    # @api.onchange('product_tmpl_id')
    # def _onchange_product_tmpl_id(self):
    #     res = super(inheritSaleOrderLine, self)._onchange_product_tmpl_id()
    #     if self.product_tmpl_id:
    #         self.hsn_id = self.product_tmpl_id.hsn_id.id
    #         self.price_unit = self.product_tmpl_id.list_price
    #         if self.order_id.partner_id.disc:
    #             self.disc_per = self.order_id.partner_id.disc
    #     return res


    @api.depends('hsn_id')
    @api.onchange('hsn_id')
    def _onchang_hsn_id(self):
        if self.order_id.business_type == 'international':
            self.gst_ids = False
        else:
            self.gst_ids = [(6, 0, self.hsn_id.hsncode_selection(self.order_id.date_order.date(),self.price_unit,self.order_id.partner_id))]
                