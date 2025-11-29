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
        return res

class inheritedPurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    cost_id = fields.Many2one('hop.cost.center',string="Cost Center")
    cost_budget = fields.Float(string="Cost Budget")

    @api.depends('product_id')
    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.cost_id = self.product_id.cost_id.id

    @api.depends('cost_id','product_id')
    @api.onchange('cost_id','product_id')
    def _onchange_cost_id(self):
        center_budget = self.env['cost.center.budget'].search([('cost_id','=',self.cost_id.id)])
        self.cost_budget = center_budget.amount if center_budget else 0
