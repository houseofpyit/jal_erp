from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta

class SaleAdvanceReceiptWiz(models.TransientModel):
    _name = 'sale.advance.receipt.wiz'
    _description =  "Sale Advance Receipt Wizard"

    mode = fields.Selection([('CHQ','CHQ'),('CASH','CASH')],string="Bank/Cash Type")
    bank_id = fields.Many2one('res.partner',string="Bank/Cash A/C")
    party_id = fields.Many2one('res.partner',string="Party")
    date = fields.Date(string="Date")
    total_amt = fields.Float("Total Amount", store=True,readonly=True,digits='Amount')
    pay_amt = fields.Float("Receipt Amount", digits='Amount')
    due_amt = fields.Float("Due Amount", store=True,readonly=True,digits='Amount')
    cheque = fields.Char(string="Cheque")
    cheque_date = fields.Date(string="Cheque Date" )
    chq_bank_id = fields.Many2one('res.partner',string="Chq Bank",domain=[('acc_type','=','BANK')])
    trn_char = fields.Char("Trn Type")

    @api.onchange('mode')
    def _onchange_mode(self):
        if self.mode == 'CHQ':
            self.trn_char = "BANK" 
            
        else:
            self.mode == 'CASH'
            self.trn_char = "CASH" 
            self.bank_id = False
            self.cheque = False
            self.cheque_date = False
            self.chq_bank_id = False

    def default_get(self, fields):
        res = super(SaleAdvanceReceiptWiz, self).default_get(fields)
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        sale_order = self.env[active_model].browse(active_id)
        
        if sale_order:
            res['party_id'] = sale_order.mapped('partner_id').id
            res['date'] = date.today()
            res['total_amt'] = sum(sale_order.mapped('net_amt'))

            receipt_rec = self.env['hop.receipt'].search([('sale_id', '=', sale_order.id)])
            adjusted_amt = sum(receipt_rec.mapped('net_amt')) if receipt_rec else 0
            
            res['due_amt'] = sum(sale_order.mapped('net_amt')) - adjusted_amt

        return res

    @api.onchange('pay_amt')
    def _onchange_pay_amt(self):
        if self.pay_amt:
            if self.pay_amt > self.due_amt:
                self.pay_amt = 0
                return {
                    'warning': {
                        'title': "Validation",
                        'message': "You Can Not Pay More Than Due Amount",
                    }
                }

    
    def action_advance_receipt(self):
        if not self.pay_amt:
            raise ValidationError("Please Enter Fist Receipt Amount")
        
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        sale_order = self.env[active_model].browse(active_id)
        bill_chr = ''
        if self.mode == 'CHQ':
            bill_chr = 'BNK'
        else:
            bill_chr = 'CSH'
        vals = {
                'bill_chr':bill_chr,
                'bill_no':self.env['hop.receipt'].sudo().bill_chr_vld(bill_chr,self.mode,self.env.company.id,self.date),
                'mode':self.mode,
                'date':self.date,
                'bank_id':self.bank_id.id,
                'party_id':sale_order.partner_id.id,
                'cheque':self.cheque,
                'chq_bank_id':self.chq_bank_id.id,
                'cheque_date':self.cheque_date,
                'vchr_type':'ADVANCE',
                'net_amt':self.pay_amt,
                'sale_id':sale_order.id
            }
        receipt = self.env['hop.receipt'].create(vals)

