{
    'name': "Jal Logistics",
    'version': "15.0",
    'summary': """ Jal Logistics """,
    'description': """ Jal Logistics """,
    'author': "",
    'company': "",
    'maintainer': "",
    'website': "",
    'category': 'Tools',
    'depends': ['base','mail','jal_crm'],
    'data': [
        'data/sequence.xml',
        'security/security_group.xml',
        'security/ir.model.access.csv',

        'report/order_form_report.xml',
        'report/paper_formate.xml',

        'views/logistics_misc_mst.xml',
        'views/logistics.xml',
        'views/inherit_sale.xml',
        'views/master_menu.xml',

    ],
    'license': "AGPL-3",
    'installable': True,
    'application': False
}
