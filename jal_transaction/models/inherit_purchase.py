from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from num2words import num2words

class inheritedPurchaseOrder(models.Model):
    _inherit = "purchase.order"

    purbill_status = fields.Selection([
        ('no_bill', 'Nothing to Bill'),
        ('waiting_bill', 'Waiting Bills'),
        ('fully_bill', 'Fully Billed'),
    ], string='Billing Status', copy=False, default='no_bill')
    is_purbill = fields.Boolean("Is Purchase Bill",compute='compute_is_purbill')

    @api.depends('picking_ids','picking_ids.purchase_bill_count','order_line.product_qty')
    def compute_is_purbill(self):
        PurchaseBillLine = self.env['hop.purchasebill.line']
        
        for rec in self:
            if not rec.picking_ids:
                rec.purbill_status = 'no_bill'
                rec.is_purbill = False
                continue

            if any(p.purchase_bill_count == 0 for p in rec.picking_ids):
                rec.purbill_status = 'waiting_bill'
                rec.is_purbill = True
                continue

            fully_billed = True

            for line in rec.order_line:
                billed_qty = sum(PurchaseBillLine.search([('order_id', '=', rec.id),('product_id', '=', line.product_id.id)]).mapped('pcs'))

                if line.product_id.is_caustic:
                    ordered_qty = sum(rec.picking_ids.move_ids_without_package.filtered(lambda ml: ml.product_id == line.product_id).mapped('actual_qty'))
                else:
                    ordered_qty = sum(rec.order_line.filtered(lambda l: l.product_id == line.product_id).mapped('product_qty'))

                if billed_qty != ordered_qty:
                    fully_billed = False
                    break

            if fully_billed:
                rec.purbill_status = 'fully_bill'
            else:
                rec.purbill_status = 'waiting_bill'

            rec.is_purbill = True


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
    
    def amount_to_text(self, amount, currency):
      if currency == 'INR':
         words = num2words(amount, lang='en_IN')
         suffix = ' Rupees'
      else:
         words = num2words(amount, lang='en')
         suffix = ''
      words = words.replace(",", " ").title()
      return f"{words}{suffix}"

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

