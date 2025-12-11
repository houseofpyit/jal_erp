{
    'name': "Jal Aqua Transaction",
    'version': "15.0",
    'summary': """ Jal Aqua Transaction """,
    'description': """ Jal Aqua Transaction """,
    'author': "",
    'company': "",
    'maintainer': "",
    'website': "",
    'category': 'Tools',
    'depends': ['base','jal_crm','transaction'],
    'data': [
        'security/user_manager.xml',
        'security/ir.model.access.csv',

        'report/report_purchase_order.xml',
        'report/paper_formate.xml',

        'views/inherit_sale.xml',
        'views/inherit_salebill.xml',
        'views/inherit_salebillreturn.xml',
        'views/inherit_partner.xml',
        'views/inherit_master.xml',
        'views/inherit_purchasebill.xml',
        'views/inherit_product.xml',
        'views/cost_center_budget.xml',
        'views/inherit_purchase.xml',
        'views/inherit_crm.xml',
        'views/master_menu.xml',

    ],
    'license': "AGPL-3",
    'installable': True,
    'application': False
}
