# -*- coding: utf-8 -*-
{
    'name': 'Performance01',
    'version': '1.1',
    'summary': 'Performance01',
    'sequence': 30,
    'description': """
        Performance01
    """,
    'category': 'E3K',
    'author': 'E3K',
    'website': '',
    'depends': ['base', 'product', 'sale', 'sale_crm', 'project'],
    'data': [
        'security/performance_security.xml',
        'security/ir.model.access.csv',
        'views/partner_view.xml',
        'views/product_view.xml',
        'views/crm_activity_view.xml',
        'views/performance_menuitem.xml',
        'report/performance_report_view.xml',
        'views/performance_analysis_export.xml',
        'wizard/performance_analysis_view.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
