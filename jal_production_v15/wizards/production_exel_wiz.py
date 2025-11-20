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

    def production_xls_report(self):
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Product Master')

        # Styles
        header_style = xlwt.easyxf(
            "pattern: pattern solid, fore_colour green; font: bold 1, colour white;"
            "align: vert centre, horiz centre; border: top thick, right thick, bottom thick, left thick;"
        )
        data_style = xlwt.easyxf(
            "align: vert centre, horiz centre; border: top thin, right thin, bottom thin, left thin;"
        )
        bold_style = xlwt.easyxf('font: bold on;')
        srl_bold_style = xlwt.easyxf("align: vert centre, horiz centre; border: top thin, right thin, bottom thin, left thin; font: bold on;")

            
        # Headers
        headers = ["Sr No.", "Product Name", "Attributes", "Name"]
        for col, head in enumerate(headers):
            sheet.write(0, col, head, header_style)
            sheet.col(col).width = 5000

        domain = [('company_id', '=', self.company_id.id)]
        
        if self.from_date:
            domain.append(('date', '>=', self.from_date))
        if self.to_date:
            domain.append(('date', '<=', self.to_date))

        production_rec = self.env['jal.production'].sudo().search(domain, order="date")

        if not production_rec:
            raise ValidationError("No Data Found.")

        row = 1
        sr_no = 1

        for rec in production_rec:
            for line in rec.finished_line_ids:

                product = line.product_id
                tmpl = product.product_tmpl_id
                attribute_lines = tmpl.attribute_line_ids

                # Write Sr No and Product name ONLY once per product
                first_row = True

                for att in attribute_lines:
                    # Values under this attribute
                    values = att.value_ids

                    # For 1st value of attribute → write attribute name
                    first_value = True

                    for val in values:

                        # Sr No & Product Name only once
                        if first_row:
                            sheet.write(row, 0, sr_no, srl_bold_style)
                            sheet.write(row, 1, product.name, bold_style)
                            first_row = False
                        else:
                            sheet.write(row, 0, "", data_style)
                            sheet.write(row, 1, "", data_style)

                        # Attribute name printed only once
                        if first_value:
                            sheet.write(row, 2, att.attribute_id.name, data_style)
                            first_value = False
                        else:
                            sheet.write(row, 2, "", data_style)

                        # Value name (always printed)
                        sheet.write(row, 3, val.name, data_style)

                        row += 1

                sr_no += 1

            # Save file
            fp = io.BytesIO()
            workbook.save(fp)
            self.rpt_xls_file = base64.encodebytes(fp.getvalue())

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{self._name}/{self.id}/rpt_xls_file/product_master.xls?download=true",
            'target': 'self',
        }
