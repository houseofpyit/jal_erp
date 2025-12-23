from odoo import api, models, fields
from datetime import date,datetime
from bs4 import BeautifulSoup 
import datetime
from odoo.tools.misc import xlwt
import base64 
import io
from odoo.exceptions import ValidationError

class SafetyExpanceExelWiz(models.TransientModel):
    _name = 'safety.expance.wiz'
    _description= "Safety Expance Exel"

    rpt_xls_file = fields.Binary()
    from_date = fields.Date(string="From Date",default=fields.Date.context_today)
    to_date = fields.Date(string="To Date",default=fields.Date.context_today)
    company_id = fields.Many2one('res.company',string="Company" , default=lambda self: self.env.company)
    product_ids = fields.Many2many('product.product',string="Product")
    cost_ids = fields.Many2many('hop.cost.center',string="Cost Center")

    def generate_xls_report(self):
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Safety Expense')

        # ---------- Styles ----------
        title_style = xlwt.easyxf(
            "font: bold 1, height 360, colour black;"
            "align: vert centre, horiz centre;"
        )

        header_style = xlwt.easyxf(
            "pattern: pattern solid, fore_colour green;"
            "font: bold 1, colour white;"
            "align: vert centre, horiz centre;"
            "border: top thick, right thick, bottom thick, left thick;"
        )

        center_style = xlwt.easyxf(
            "align: vert centre, horiz centre;"
            "border: top thin, right thin, bottom thin, left thin;"
        )

        date_style = xlwt.easyxf(
            "align: vert centre, horiz centre;"
            "border: top thin, right thin, bottom thin, left thin;",
            num_format_str='DD/MM/YYYY'
        )

        # ---------- Title ----------
        worksheet.row(0).height = 600   # margin / height
        worksheet.write_merge(
            0, 0,          # row start, row end
            0, 10,         # col start, col end (11 columns)
            "SAFETY EXPANCE",
            title_style
        )

        # ---------- Headers ----------
        headers = [
            "PO NUMBER","DATE","VENDOR NAME","COST CENTER",
            "MATERIAL DETAIL","QTY","RATE","TAXABLEVALUE","GST","BUDGET","BALANCE"
        ]

        worksheet.row(1).height = 500

        for col, header in enumerate(headers):
            worksheet.write(1, col, header, header_style)
            worksheet.col(col).width = 6000

        # ---------------- SQL QUERY ----------------

        query = """
            SELECT
                po.name                     AS po_number,
                po.date_order::date         AS po_date,
                rp.name                     AS vendor_name,
                cc.name                     AS cost_center,

                pol.product_id              AS product_id,

                SUM(pol.product_qty)        AS qty,
                pol.price_unit              AS rate,
                SUM(pol.taxablevalue)       AS taxablevalue,
                SUM(pol.price_tax)          AS gst,
                MAX(cb.amount)              AS budget,
                MAX(cb.amount) - SUM(pol.taxablevalue) AS balance

            FROM purchase_order po
            JOIN res_partner rp ON rp.id = po.partner_id
            JOIN purchase_order_line pol ON pol.order_id = po.id

            LEFT JOIN hop_cost_center cc ON cc.id = pol.cost_id
            LEFT JOIN cost_center_budget cb ON cb.cost_id = cc.id

            JOIN product_product pp ON pp.id = pol.product_id

            WHERE po.company_id = %s
            AND po.date_order::date BETWEEN %s AND %s
            AND po.state IN ('purchase','done')
        """


        params = [
            self.company_id.id,
            self.from_date,
            self.to_date
        ]

        if self.product_ids:
            query += " AND pol.product_id IN %s"
            params.append(tuple(self.product_ids.ids))

        if self.cost_ids:
            query += " AND pol.cost_id IN %s"
            params.append(tuple(self.cost_ids.ids))

        query += """
            GROUP BY
                po.name,
                po.date_order,
                rp.name,
                cc.name,
                pol.product_id,  
                pol.price_unit
            ORDER BY po.date_order, po.name
        """


        # Execute
        self.env.cr.execute(query, tuple(params))
        records = self.env.cr.fetchall()

        # Write rows
        row = 2
        for rec in records:
            for col, value in enumerate(rec):
                if col == 1 and value:  # po_date
                    worksheet.write(row, col, value, date_style)
                else:
                    if col == 4 and value:
                        product = self.env['product.product'].browse(value)
                        material_detail = product.display_name if product.display_name else ''
                        worksheet.write(row, col, material_detail or '', center_style)
                    else:
                        worksheet.write(row, col, value or '', center_style)
            row += 1

        # Save file
        fp = io.BytesIO()
        workbook.save(fp)
        self.rpt_xls_file = base64.b64encode(fp.getvalue())

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/safety.expance.wiz/%s/rpt_xls_file/safety_expense_excel.xls?download=true' % self.id,
            'target': 'self',
        }
