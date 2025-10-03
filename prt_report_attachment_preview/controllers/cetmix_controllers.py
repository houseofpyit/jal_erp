import json

from odoo import http
from odoo.http import request
from odoo.tools.safe_eval import safe_eval, time

from odoo.addons.http_routing.models.ir_http import slugify
from odoo.addons.web.controllers.main import ReportController


class CxReportController(ReportController):
    def _prepare_filepart(self, doc_ids, report):
        """Prepare filename for report"""
        if doc_ids:
            doc_ids_len = len(doc_ids)
            if doc_ids_len > 1:
                model_id = request.env["ir.model"].sudo()._get(report.model)
                return f"{model_id.name} (x{doc_ids_len})"
            report_name = report.print_report_name
            if doc_ids_len == 1 and report_name:
                obj = request.env[report.model].sudo().browse(doc_ids)
                return safe_eval(report_name, {"object": obj, "time": time})
        return "report"

    @http.route(
        [
            "/report/<converter>/<reportname>",
            "/report/<converter>/<reportname>/<docids>",
        ],
        type="http",
        auth="user",
        website=True,
    )
    def report_routes(self, reportname, docids=None, converter=None, **data):
        """
        Overwrite method to open PDF report in new window
        """
        if converter != "pdf":
            return super().report_routes(
                reportname, docids=docids, converter=converter, **data
            )
        report = request.env["ir.actions.report"].sudo()._get_report_from_name(reportname)
        context = dict(request.env.context)
        if docids:
            docids = [int(i) for i in docids.split(",")]
        if data.get("options"):
            data.update(json.loads(data.pop("options")))
        if data.get("context"):
            data["context"] = json.loads(data["context"])
            context.update(data["context"])
        # Get filename for report
        filepart = self._prepare_filepart(docids, report)
        pdf = report.with_context(**context).sudo()._render_qweb_pdf(docids, data=data)[0]
        return request.make_response(
            pdf,
            headers=[
                ("Content-Type", "application/pdf"),
                ("Content-Length", len(pdf)),
                (
                    "Content-Disposition",
                    'inline; filename="%s.pdf"' % slugify(filepart),
                ),
            ],
        )
