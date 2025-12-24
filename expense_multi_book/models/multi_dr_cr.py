from odoo import models, fields, api, _
from datetime import datetime , date


class HopMultiDrCr(models.Model):
    _name = "hop.multi.dr.cr"
    _description = "Multi DR-CR"
    _inherit = ['mail.thread','financial.year.abstract']


    name = fields.Char(string="Serial No.", readonly=True,copy=False)
    bill_chr = fields.Char(default="MDC")
    bill_no =  fields.Integer(required=True,copy=False)
    company_id = fields.Many2one("res.company", string="Company",required=True, default=lambda self: self.env.company.id)
    date = fields.Date(string='Date',default=fields.Date.context_today)
    expense_id = fields.Many2one('res.partner',string="Expense")
    line_ids = fields.One2many('hop.multi.dr.cr.line',"mst_id",string="Line")
    is_mismatch_amt = fields.Boolean(string="Show Mismatch Alert", compute="_compute_show_mismatch_alert")

    def unlink(self):
        for line in self:
            line.line_ids.unlink()
            # Your cleanup logic here
        return super(HopMultiDrCr, self).unlink()

    @api.depends('line_ids')
    def _compute_show_mismatch_alert(self):
        for record in self:
            total_cr = round(sum(record.line_ids.mapped('cr_amount')),2)
            total_dr = round(sum(record.line_ids.mapped('dr_amount')),2)
            record.is_mismatch_amt = total_cr != total_dr


    @api.model
    def default_get(self, fields):
        res = super(HopMultiDrCr, self).default_get(fields)
        res['bill_no'] = self.bill_chr_vld()
        res['date'] = datetime.now()
        return res
    
    @api.onchange('bill_chr','bill_no')
    def _onchange_chr_no(self):
        if self.bill_chr:
            self.name = str(self.bill_chr)+ str(self.bill_no)
        else:
            self.name = self.bill_no

    @api.model
    def create(self, vals):
        if vals.get('bill_no') == None:
            vals['bill_no'] = self.bill_chr_vld()

        res = super(HopMultiDrCr, self).create(vals)
        res._onchange_chr_no()
        return res

    @api.onchange('bill_chr')
    def _onchange_bill_chr(self):
        self.bill_no = self.bill_chr_vld()

    def bill_chr_vld(self):
        query = ''' Select max(bill_no) From hop_multi_dr_cr Where company_id = ''' + str(self.env.company.id)
        if self.bill_chr:
            query += " and bill_chr = '" + self.bill_chr + "'"
        else:
            query += " and bill_chr IS NULL"
        if self.env.user.fy_year_id:
            query += " and date >=  " +"'" + str(self.env.user.fy_from_date) +"'"
            query += " and date <=  " +"'" + str(self.env.user.fy_to_date) +"'"

        self.env.cr.execute(query)
        query_result = self.env.cr.dictfetchall()
        if query_result[0]['max'] == None :
            serial = 1
        else:
            serial = 1 + query_result[0]['max']
        return serial
    
    @api.onchange('line_ids','bill_no','date')
    def onchange_line_ids(self):
        for line in self.line_ids:
            if self.date:
                line.date = self.date
            if self.bill_chr:
                line.bill_chr = self.bill_chr
            if self.bill_no:
                line.bill_no = self.bill_no
            if self.name:
                line.name = self.name
            # if self.expense_id:
            #     line.expense_id = self.expense_id.id
    

class HopMultiDrCrLine(models.Model):
    _name = "hop.multi.dr.cr.line"
    _description= "Multi Dr Cr Line"
    _inherit = ['mail.thread','financial.year.abstract','ledger.data.set.abstract']

    mst_id = fields.Many2one ('hop.multi.dr.cr','Master',ondelete='cascade')
    ac_id = fields.Many2one('res.partner',string="Account",required=True,tracking=True)
    ref_ac_id = fields.Many2one('res.partner',string="Ref. Account",required=True,tracking=True)
    remarks = fields.Char(string="Narration")
    cr_amount = fields.Float(string="CR Amount",digits='Amount')
    dr_amount = fields.Float(string="DR Amount",digits='Amount')
    trn_mode = fields.Selection([
        ('CREDIT','CREDIT'),
        ('DEBIT','DEBIT'),
        ],string='Trn Mode',tracking=True)

    name = fields.Char(string="Serial No.",copy=False)
    bill_chr = fields.Char(default="MDC")
    bill_no =  fields.Integer(copy=False)
    date = fields.Date(string='Date')

