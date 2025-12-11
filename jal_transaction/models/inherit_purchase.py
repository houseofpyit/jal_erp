from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class inheritedPurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_bill(self):
        res = super(inheritedPurchaseOrder, self).action_bill()
        for line in self.order_line:
            purc_bill_line = self.env['hop.purchasebill.line'].search([('order_id','=',self.id),('product_id','=',line.product_id.id)])
            if purc_bill_line:
                purc_bill_line.write({'cost_center_id':line.cost_id.id})

        purc_bill_line = self.env['hop.purchasebill.line'].search([('order_id','=',self.id)],limit=1)
        purc_bill = self.env['hop.purchasebill'].search([('id','=',purc_bill_line.mst_id.id)]) if purc_bill_line else False
        if purc_bill:
            purc_bill.rd_urd = self.partner_id.rd_urd
            purc_bill.due_days = self.partner_id.due_days
        return res

class inheritedPurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    cost_id = fields.Many2one('hop.cost.center',string="Cost Center")
    cost_budget = fields.Float(string="Cost Budget")

    @api.depends('product_id')
    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.cost_id = self.product_id.cost_id.id

    @api.onchange('cost_id','product_id')
    def _onchange_cost_id(self):
        for rec in self:
            if not rec.cost_id:
                rec.cost_budget = 0
                continue

            center_budget = self.env['cost.center.budget'].search([('cost_id', '=', rec.cost_id.id)],limit=1)

            budget_amount = center_budget.amount if center_budget else 0
            
            used_amount = sum(self.env['purchase.order.line'].search([('cost_id', '=', rec.cost_id.id)]).mapped('taxablevalue'))

            if used_amount:
                rec.cost_budget = budget_amount - used_amount
            else:
                rec.cost_budget = budget_amount

