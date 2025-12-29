from odoo import api, models, fields
from datetime import date,datetime
from bs4 import BeautifulSoup 
import datetime
from odoo.tools.misc import xlwt
import base64 
import io
from odoo.exceptions import ValidationError
from datetime import timedelta

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
        
        StockMoveLine = self.env['stock.move.line'].sudo()
        OPStock = self.env['hop.op.stock.mst'].sudo()

        # ==========================
        # Dynamic Product List
        # ==========================
        raw_products = list(set(production_rec.line_ids.mapped('product_id')))
        raw_products = sorted(raw_products, key=lambda p: p.display_name)
        raw_products += list(set(production_rec.mapped('product_tmpl_id')))
        # Headers        

        sheet.write(0, 0, "", header_style)   # first column blank

        col = 1
        for p in raw_products:
            # Merge 1 row (row 0), 4 columns (col → col+3)
            sheet.write_merge(0, 0, col, col + 3, p.display_name, header_style)

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
        headers2 = ["Opening", "Production", "Dispatch", "Closing"]
        
        for p in raw_products:
            headers = headers2 if p == raw_products[-1] else headers1

            for h in headers:
                sheet.write(1, col, h, header_style)
                col += 1

        row = 2   # data starts from row 2

        date_list = sorted(list(set(production_rec.mapped('date'))))

        op_name = OPStock.search([]).mapped('name')
        op_name_receipt = [f"{n} - Receipt"  for n in op_name]

        for prod_date in date_list:

            date_recs = production_rec.filtered(lambda r: r.date == prod_date)

            # Write Date
            sheet.write(row, 0, prod_date.strftime("%d/%m/%Y"), data_style)

            col = 1

            for prod in raw_products:

                # FILTER product lines for this date
                prod_lines = date_recs.line_ids.filtered(lambda l: l.product_id.id == prod.id)

                opening = 0
                closing = 0
                receiving = 0
                consumption = 0
                production = 0
                dispatch = 0

                # =========================
                # RECEIVING (Incoming Pickings)
                # =========================
                start_dt = prod_date.strftime('%Y-%m-%d 00:00:00')
                end_dt = prod_date.strftime('%Y-%m-%d 23:59:59')
                incoming_moves = StockMoveLine.search([
                    ('product_id', '=', prod.id),
                    ('picking_id.picking_type_code', '=', 'incoming'),
                    ('picking_id.state', '=', 'done'),
                    ('picking_id.date_done', '>=', start_dt),
                    ('picking_id.date_done', '<=', end_dt),
                    ('picking_id.origin', 'not in', op_name_receipt),
                ])
                receiving = sum(incoming_moves.filtered(lambda l: l.product_id.id == prod.id).mapped('qty_done'))

                opincoming_moves = StockMoveLine.search([
                    ('product_id', '=', prod.id),
                    ('picking_id.picking_type_code', '=', 'incoming'),
                    ('picking_id.state', '=', 'done'),
                    ('picking_id.date_done', '>=', start_dt),
                    ('picking_id.date_done', '<=', end_dt),
                    ('picking_id.origin', 'in', op_name_receipt),
                ])

                opening = sum(opincoming_moves.filtered(lambda l: l.product_id.id == prod.id).mapped('qty_done'))

                start_dt_data = fields.Datetime.from_string(start_dt)
                end_dt_data   = fields.Datetime.from_string(end_dt)

                last_start_dt = start_dt_data - timedelta(days=1)
                last_end_dt = end_dt_data - timedelta(days=1) 

                closing_incoming_moves = StockMoveLine.search([
                    ('product_id', '=', prod.id),
                    ('picking_id.picking_type_code', '=', 'incoming'),
                    ('picking_id.state', '=', 'done'),
                    ('picking_id.date_done', '>=', last_start_dt),
                    ('picking_id.date_done', '<=', last_end_dt),
                    ('picking_id.origin', 'not in', op_name_receipt),
                ])
                closing_receiving = sum(closing_incoming_moves.filtered(lambda l: l.product_id.id == prod.id).mapped('qty_done'))

                closing_opincoming_moves = StockMoveLine.search([
                    ('product_id', '=', prod.id),
                    ('picking_id.picking_type_code', '=', 'incoming'),
                    ('picking_id.state', '=', 'done'),
                    ('picking_id.date_done', '>=', last_start_dt),
                    ('picking_id.date_done', '<=', last_end_dt),
                    ('picking_id.origin', 'in', op_name_receipt),
                ])

                closing_opening = sum(closing_opincoming_moves.filtered(lambda l: l.product_id.id == prod.id).mapped('qty_done'))

                last_prod_date = prod_date - timedelta(days=1) 

                last_date_recs = production_rec.filtered(lambda r: r.date == last_prod_date)

                last_prod_lines = last_date_recs.line_ids.filtered(lambda l: l.product_id.id == prod.id)
                
                # =========================
                # NORMAL PRODUCTS
                # =========================
                if prod != raw_products[-1]:
                    consumption = sum(prod_lines.mapped('qty'))

                    closing =  ((closing_receiving + closing_opening) - sum(last_prod_lines.mapped('qty'))) if (closing_receiving + closing_opening) > 0 else 0
                    closing_str = "{:.2f}".format(closing)

                    sheet.write(row, col,     opening,     data_style)
                    sheet.write(row, col + 1, receiving,   data_style)
                    sheet.write(row, col + 2, consumption, data_style)
                    sheet.write(row, col + 3, closing_str, data_style)

                # =========================
                # LAST PRODUCT (FINISHED GOODS)
                # =========================
                else:
                    finished_lines = date_recs.finished_line_ids.filtered(
                        lambda f: f.mst_id.product_tmpl_id.id == prod.id
                    )

                    production = sum(finished_lines.mapped('bucket_qty'))

                    # Optional: Dispatch (outgoing)
                    start_dt = prod_date.strftime('%Y-%m-%d 00:00:00')
                    end_dt = prod_date.strftime('%Y-%m-%d 23:59:59')
                    outgoing_moves = StockMoveLine.search([
                        ('product_id', '=', prod.id),
                        ('picking_id.picking_type_code', '=', 'outgoing'),
                        ('picking_id.state', '=', 'done'),
                        ('picking_id.date_done', '>=', start_dt),
                        ('picking_id.date_done', '<=', end_dt),
                    ])
                    dispatch = sum(outgoing_moves.filtered(lambda l: l.product_id.id == prod.id).mapped('qty_done'))

                    closing_outgoing_moves = StockMoveLine.search([
                        ('product_id', '=', prod.id),
                        ('picking_id.picking_type_code', '=', 'outgoing'),
                        ('picking_id.state', '=', 'done'),
                        ('picking_id.date_done', '>=', last_start_dt),
                        ('picking_id.date_done', '<=', last_end_dt),
                    ])
                    closing_dispatch = sum(closing_outgoing_moves.filtered(lambda l: l.product_id.id == prod.id).mapped('qty_done'))

                    last_finished_lines = last_date_recs.finished_line_ids.filtered(
                        lambda f: f.mst_id.product_tmpl_id.id == prod.id
                    )
                    last_production = sum(last_finished_lines.mapped('bucket_qty'))

                    closing =  ((closing_opening + last_production) - closing_dispatch) if (closing_receiving + last_production) > 0 else 0
                    closing_str = "{:.2f}".format(closing)

                    sheet.write(row, col,     opening,    data_style)
                    sheet.write(row, col + 1, production, data_style)
                    sheet.write(row, col + 2, dispatch,   data_style)
                    sheet.write(row, col + 3, closing_str,    data_style)

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
    

class Production2ReportExelWiz(models.TransientModel):
    _name = 'production2.exel.wiz'
    _description= "Daily Production Report Exel"

    rpt_xls_file = fields.Binary()
    from_date = fields.Date(string="From Date",default=fields.Date.context_today)
    to_date = fields.Date(string="To Date",default=fields.Date.context_today)
    company_id = fields.Many2one('res.company',string="Company" , default=lambda self: self.env.company)

    def production_xls_report(self):
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Stock')

        header_style = xlwt.easyxf(
            "font: bold 1, colour black;"
            "align: vert centre, horiz centre;"
            "border: top thick, right thick, bottom thick, left thick;"
        )
        center_style = xlwt.easyxf(
            "align: vert centre, horiz centre; border: top thin, right thin, bottom thin, left thin;"
        )

        headers = ["DATE", "PRODUCTION", "PRODUCT NAME", "NO OF DRUM", "WEIGHT"]
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_style)
            worksheet.col(col).width = 5000

        row = 1
        srl = 1
        domain = [('company_id', '=', self.company_id.id)]
        if self.from_date:
            domain.append(('date', '>=', self.from_date))
        if self.to_date:
            domain.append(('date', '<=', self.to_date))
        
        production_rec = self.env['jal.production'].sudo().search(domain, order="date")

        if not production_rec:
            raise ValidationError("No Data !!!")

        for rec in production_rec:
            worksheet.write(row, 0, rec.date.strftime('%d-%m-%Y') if rec.date else '', center_style)  
            worksheet.write(row, 1, rec.name or "", center_style)
            worksheet.write(row, 2, rec.product_tmpl_id.display_name or "", center_style)
            worksheet.write(row, 3, sum(rec.finished_line_ids.mapped('bucket_qty')) or 0, center_style)
            worksheet.write(row, 4, sum(rec.finished_line_ids.mapped('qty')) or 0, center_style)

            row += 1
            srl += 1

        fp = io.BytesIO()
        workbook.save(fp)
        self.rpt_xls_file = base64.encodebytes(fp.getvalue())

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{self._name}/{self.id}/rpt_xls_file/daily_production_report_excel.xls?download=true",
            'target': 'self',
        }