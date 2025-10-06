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
        # 'security/ir.model.access.csv',

        'views/inherit_sale.xml',
        'views/inherit_salebill.xml',
        'views/inherit_salebillreturn.xml',
        'views/inherit_partner.xml',
        'views/master_menu.xml',

    ],
    'license': "AGPL-3",
    'installable': True,
    'application': False
}
