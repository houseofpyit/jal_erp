from odoo import api, models, fields, _
from odoo.tests import Form, tagged
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date


class InheritHOPGenPurchase(models.Model):
    _inherit = "hop.gen.purchase"

    purchase_id = fields.Many2one('purchase.order',"Purchase ID",tracking=True)
    party_id = fields.Many2one('res.partner',"Party",domain=['|',('acc_type','=','GENERAL_PURCHASE_PARTY'),('is_common','=',True)],required=True,tracking=True)
    gst_no = fields.Char('GST No.',related='party_id.gstno')
    single_multi_book = fields.Selection([
        ('Single_Book', 'Single Book'),
        ('Multi_Book', 'Multi Book'),
    ], string="Book Select", default="Single_Book")
    tot_summary_amt = fields.Float("Amount",compute='_total_amt_calculate', store=True,readonly=True,digits='Amount')
    summary_ids = fields.One2many('hop.summary.line', 'summary_id', string="Summary")
    is_mismatch_amt = fields.Boolean(string="Show Mismatch Alert", compute="_compute_show_mismatch_alert", store=True)

    @api.depends('tot_taxable', 'tot_summary_amt')
    def _compute_show_mismatch_alert(self):
        for record in self:
            record.is_mismatch_amt = False
            if record.single_multi_book == 'Multi_Book' and record.tot_taxable > 0:
                record.is_mismatch_amt = record.tot_taxable != record.tot_summary_amt

    @api.depends('summary_ids')
    def _total_amt_calculate(self):
        for i in self:
            i.tot_summary_amt = sum(i.summary_ids.mapped('total_amount'))

    @api.model
    def create(self, vals):
        record = super(InheritHOPGenPurchase, self).create(vals)
        if 'line_id' in vals:
            summary_lines = []
            for book in record.line_id.mapped('book_id'):
                total_amount = sum(record.line_id.filtered(lambda l: l.book_id == book).mapped('taxablevalue'))
                summary_lines.append((0, 0, {
                    'book_id': book.id,
                    'name': record.name,
                    'bill_no': record.bill_no,
                    'bill_chr': record.bill_chr,
                    'date': record.date,
                    'party_id': record.party_id.id,
                    'bill_number': record.bill_number,
                    'total_amount': total_amount,
                    'single_multi_book':record.single_multi_book,
                }))
            record.write({'summary_ids': summary_lines})
        return record


    def write(self, vals):
        result = super(InheritHOPGenPurchase, self).write(vals)
        if 'line_id' in vals:
            for record in self:
                summary_lines = []
                for book in record.line_id.mapped('book_id'):
                    ex_line = self.summary_ids.filtered(lambda l: l.book_id == book)
                    if ex_line:
                        total_amount = sum(record.line_id.filtered(lambda l: l.book_id == book).mapped('taxablevalue'))
                        ex_line.write({
                        'book_id': book.id,
                        'name': record.name,
                        'bill_no': record.bill_no,
                        'bill_chr': record.bill_chr,
                        'date': record.date,
                        'party_id': record.party_id.id,
                        'bill_number': record.bill_number,
                        'total_amount': total_amount,
                        'single_multi_book':record.single_multi_book,
                        })
                    else:
                        total_amount = sum(record.line_id.filtered(lambda l: l.book_id == book).mapped('taxablevalue'))
                        summary_lines.append((0, 0, {
                            'book_id': book.id,
                            'name': record.name,
                            'bill_no': record.bill_no,
                            'bill_chr': record.bill_chr,
                            'date': record.date,
                            'party_id': record.party_id.id,
                            'bill_number': record.bill_number,
                            'total_amount': total_amount,
                            'single_multi_book':record.single_multi_book,
                        }))
                record.summary_ids = summary_lines
        self.summary_ids.filtered(lambda l: l.book_id.id not in self.line_id.mapped('book_id').ids).unlink()
        return result
    
    @api.onchange('name','bill_no','bill_chr','date','party_id','bill_number')
    def _onchange_name(self):
        if self.name:
            self.summary_ids.name = self.name
        if self.bill_no:
            self.summary_ids.bill_no = self.bill_no
        if self.bill_chr:
            self.summary_ids.bill_chr = self.bill_chr
        if self.date:
            self.summary_ids.date = self.date
        if self.party_id:
            self.summary_ids.party_id = self.party_id
        if self.bill_number:
            self.summary_ids.bill_number = self.bill_number
        if self.single_multi_book:
            self.summary_ids.single_multi_book = self.single_multi_book

class InheritHOPGenPurchase_line(models.Model):
    _inherit = "hop.gen.purchase.line"

    cost_id = fields.Many2one('hop.cost.center',string="Cost Center")
    book_id = fields.Many2one('res.partner',"Book",domain=[('acc_type','=','GENERAL_PURCHASE_BOOK')],required=True,tracking=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        super(InheritHOPGenPurchase_line,self)._onchange_product_id()
        self.cost_id = self.product_id.cost_id.id

class HopSummaryLine(models.Model):
    _name = "hop.summary.line"
    _inherit = ['mail.thread','financial.year.abstract','ledger.data.set.abstract']

    summary_id = fields.Many2one('hop.gen.purchase', string="Summary",ondelete='cascade')
    name = fields.Char(string="Purchase Bill",copy=False,tracking=True)
    bill_no =  fields.Integer(required=True,copy=False,tracking=True)
    bill_chr = fields.Char("Bill No",tracking=True)
    date = fields.Date(string='Date', default=fields.Date.context_today,tracking=True)
    party_id = fields.Many2one('res.partner',"Party",domain=[('acc_type','=','GENERAL_PURCHASE_PARTY')],required=True,tracking=True)
    bill_number = fields.Char("Party Bill No.",tracking=True)
    book_id = fields.Many2one('res.partner',"Book",domain=[('acc_type','=','GENERAL_PURCHASE_BOOK')],required=True,tracking=True)
    total_amount = fields.Float('Total Amount')
    single_multi_book = fields.Selection([
        ('Single_Book', 'Single Book'),
        ('Multi_Book', 'Multi Book'),], string="Book Select", default="Single_Book")
    company_id = fields.Many2one("res.company", string="Company",required=True, default=lambda self: self.env.company.id)