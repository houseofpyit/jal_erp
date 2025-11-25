from odoo import api, models, fields
from datetime import date,datetime
from bs4 import BeautifulSoup 
import datetime
from odoo.tools.misc import xlwt
import base64 
import io
from odoo.exceptions import ValidationError

class ProductionReportExelWiz(models.TransientModel):
    _name = 'production.exel.wiz'
    _description= "Production Report Exel"

    rpt_xls_file = fields.Binary()
    from_date = fields.Date(string="From Date",default=fields.Date.context_today)
    to_date = fields.Date(string="To Date",default=fields.Date.context_today)
    company_id = fields.Many2one('res.company',string="Company" , default=lambda self: self.env.company)
    shift_ids = fields.Many2many('shift.mst',string="Shift")

    def production_xls_report(self):
        workbook = xlwt.Workbook()

        # ===============================#
        #           SHEET 1
        # ===============================#
        sheet = workbook.add_sheet('Shift Wise Report')

        # Styles
        header_style = xlwt.easyxf(
            "font: bold 1, colour black;"
            "align: vert centre, horiz centre;"
            "border: top thick, right thick, bottom thick, left thick;"
        )
        data_style = xlwt.easyxf(
            "align: vert centre, horiz centre; border: top thin, right thin, bottom thin, left thin;"
        )
        srl_bold_style = xlwt.easyxf(
            "align: vert centre, horiz centre; border: top thin, right thin, bottom thin, left thin; font: bold on;"
        )

        # Domain Filter
        domain = [('company_id', '=', self.company_id.id)]
        if self.from_date:
            domain.append(('date', '>=', self.from_date))
        if self.to_date:
            domain.append(('date', '<=', self.to_date))
        if self.shift_ids:
            domain.append(('shift_id', 'in', self.shift_ids.ids))
        
        production_rec = self.env['jal.production'].sudo().search(domain, order="date")
        
        if not production_rec:
            raise ValidationError("No Data Found.")

        # ==========================
        # Dynamic Product List
        # ==========================
        raw_products = list(set(production_rec.line_ids.mapped('product_id')))
        raw_products = sorted(raw_products, key=lambda p: p.name)
        
        # Headers
        headers = ["Date", "Shift"] + [p.name for p in raw_products] + ["Total Production (MT)"]

        # Write Header - Sheet 1
        for col, head in enumerate(headers):
            sheet.write(0, col, head, header_style)
            sheet.col(col).width = 5000

        row = 1

        # Unique Dates
        date_list = sorted(list(set(production_rec.mapped('date'))))
        
        # ==================================#
        #       LOOP DATE-WISE
        # ==================================#
        last_date = None   # <-- Put this BEFORE the for prod_date

        for prod_date in date_list:

            date_recs = production_rec.filtered(lambda r: r.date == prod_date)
            shift_list = sorted(list(set(date_recs.mapped('shift_id'))), key=lambda s: s.name)

            for shift in shift_list:

                rec = date_recs.filtered(lambda r: r.shift_id.id == shift.id)
                if not rec:
                    continue

                rec = rec[0]

                # ----------------------------------
                # PRINT DATE ONLY ON FIRST OCCURRENCE
                # ----------------------------------
                date_str = prod_date.strftime('%d-%m-%Y')

                if last_date != date_str:
                    sheet.write(row, 0, date_str, srl_bold_style)
                    last_date = date_str
                else:
                    sheet.write(row, 0, "", srl_bold_style)
                # sheet.write(row, 0, str(prod_date), data_style)
                sheet.write(row, 1, shift.name, data_style)

                col = 2
                for prod in raw_products:
                    qty = sum(
                        date_recs.mapped('line_ids').filtered(
                            lambda l: l.product_id.id == prod.id and
                                    l.mst_id.shift_id.id == shift.id
                        ).mapped('qty')
                    )

                    sheet.write(row, col, qty, data_style)
                    col += 1

                total_mt = sum(
                    date_recs.mapped('finished_line_ids').filtered(
                        lambda l: l.mst_id.shift_id.id == shift.id
                    ).mapped('qty')
                )

                sheet.write(row, col, total_mt, srl_bold_style)
                row += 1

        # ==========================
        # SAVE FILE
        # ==========================

        fp = io.BytesIO()
        workbook.save(fp)
        self.rpt_xls_file = base64.encodebytes(fp.getvalue())

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{self._name}/{self.id}/rpt_xls_file/Shift_wise_report.xls?download=true",
            'target': 'self',
        }


class Production1ReportExelWiz(models.TransientModel):
    _name = 'production1.exel.wiz'
    _description= "Day Wise Report"

    rpt_xls_file = fields.Binary()
    from_date = fields.Date(string="From Date",default=fields.Date.context_today)
    to_date = fields.Date(string="To Date",default=fields.Date.context_today)
    company_id = fields.Many2one('res.company',string="Company" , default=lambda self: self.env.company)

    def production_xls_report(self):
        workbook = xlwt.Workbook()

        # ===============================#
        #           SHEET 1
        # ===============================#
        sheet = workbook.add_sheet('Shift Wise Report')

        # Styles
        header_style = xlwt.easyxf(
            "font: bold 1, colour black;"
            "align: vert centre, horiz centre;"
            "border: top thick, right thick, bottom thick, left thick;"
        )
        data_style = xlwt.easyxf(
            "align: vert centre, horiz centre; border: top thin, right thin, bottom thin, left thin;"
        )
        srl_bold_style = xlwt.easyxf(
            "align: vert centre, horiz centre; border: top thin, right thin, bottom thin, left thin; font: bold on;"
        )

        # Domain Filter
        domain = [('company_id', '=', self.company_id.id)]
        if self.from_date:
            domain.append(('date', '>=', self.from_date))
        if self.to_date:
            domain.append(('date', '<=', self.to_date))
        
        production_rec = self.env['jal.production'].sudo().search(domain, order="date")
        
        if not production_rec:
            raise ValidationError("No Data Found.")

        # ==========================
        # Dynamic Product List
        # ==========================
        raw_products = list(set(production_rec.line_ids.mapped('product_id')))
        raw_products = sorted(raw_products, key=lambda p: p.name)
        
        # Headers        

        sheet.write(0, 0, "", header_style)   # first column blank

        col = 1
        for p in raw_products:
            # Merge 1 row (row 0), 4 columns (col → col+3)
            sheet.write_merge(0, 0, col, col + 3, p.name, header_style)

            # Set column widths
            sheet.col(col).width = 5000
            sheet.col(col + 1).width = 5000
            sheet.col(col + 2).width = 5000
            sheet.col(col + 3).width = 5000

            col += 4   # jump by 4 columns for next product


        # Second Header Row
        sheet.write(1, 0, "Date", header_style)

        col = 1
        headers1 = ["Opening", "Receiving", "Consumption", "Closing"]

        for p in raw_products:
            for h in headers1:
                sheet.write(1, col, h, header_style)
                col += 1

        row = 2   # data starts from row 2

        date_list = sorted(list(set(production_rec.mapped('date'))))

        for prod_date in date_list:

            date_recs = production_rec.filtered(lambda r: r.date == prod_date)

            # Write Date
            sheet.write(row, 0, prod_date.strftime("%d/%m/%Y"), data_style)

            col = 1

            for prod in raw_products:

                # FILTER product lines for this date
                prod_lines = date_recs.line_ids.filtered(lambda l: l.product_id.id == prod.id)

                # === CALCULATIONS ===
                opening = 0
                receiving = 0
                consumption = sum(prod_lines.mapped('qty'))         
                closing = 0

                # === WRITE TO SHEET ===
                sheet.write(row, col,     opening,     data_style)
                sheet.write(row, col + 1, receiving,   data_style)
                sheet.write(row, col + 2, consumption, data_style)
                sheet.write(row, col + 3, closing,     data_style)

                col += 4

            row += 1

        # ==========================
        # SAVE FILE
        # ==========================

        fp = io.BytesIO()
        workbook.save(fp)
        self.rpt_xls_file = base64.encodebytes(fp.getvalue())

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{self._name}/{self.id}/rpt_xls_file/Shift_wise_report.xls?download=true",
            'target': 'self',
        }