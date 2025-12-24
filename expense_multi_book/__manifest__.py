{
    'name': "Expense Multi Book",
    'version': "15.0",
    'summary': """ Expense Multi Book """,
    'description': """ Expense Multi Book """,
    'author': "",
    'company': "",
    'maintainer': "",
    'website': "",
    'category': 'Tools',
    'depends': ['base','transaction','hop_account'],
    'data': [
        'data/purchase_led_data.xml',
        'data/multy_cr_dr_data.xml',
        'security/ir.model.access.csv',

        'views/inherit_gen_purchase.xml',
        'views/multi_dr_cr.xml',
        'views/menu_view.xml',

    ],
    'license': "AGPL-3",
    'installable': True,
    'application': False
}
