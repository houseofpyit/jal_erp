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
    'depends': ['base','transaction'],
    'data': [
        'data/purchase_led_data.xml',
        'security/ir.model.access.csv',

        'views/inherit_gen_purchase.xml',

    ],
    'license': "AGPL-3",
    'installable': True,
    'application': False
}
