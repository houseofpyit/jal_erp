{
    "name": "Open PDF Reports and PDF Attachments in Browser",
    "version": "15.0",
    "summary": """
    Preview reports and pdf attachments in browser instead of downloading them.
    Open Report or PDF Attachment in new tab instead of downloading.
""",
    "author": "House of PY Technologies",
    "category": "Productivity",
    "license": "LGPL-3",
    "website": "http://houseofpy.com/",
    # "live_test_url": "https://demo.cetmix.com",
    "depends": ["web"],
    "images": ["static/description/banner.png"],
    "assets": {
        "web.assets_backend": [
            "prt_report_attachment_preview/static/src/js/tools.esm.js",
            "prt_report_attachment_preview/static/src/js/report.esm.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
