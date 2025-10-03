{
    'name': "Jal Production",
    'version': "15.0",
    'summary': """ Jal Production """,
    'description': """ Jal Production """,
    'author': "",
    'company': "",
    'maintainer': "",
    'website': "",
    'category': 'Tools',
    'depends': ['base','stock'],
    'data': [
        'data/sequence.xml',
        'security/security_group.xml',
        'security/ir.model.access.csv',
        'security/record_rule.xml',

        'views/production.xml',
        'views/quality.xml',
        'views/shift_mst.xml',
        'views/inherit_product.xml',
        'views/quality_parameter_mst.xml',
        'views/master_menu.xml',

    ],
    'license': "AGPL-3",
    'installable': True,
    'application': False
}
