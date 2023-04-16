{
    'name': 'Consignment Invoicing',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Invoicing for consignment products',
    'depends': ['sale', 'account'],
    'author': 'Your Company',
    'license': 'AGPL-3',
    'website': 'https://www.yourcompany.com',
    'description': """
Consignment Invoicing
=====================

This module provides a way to invoice consignment products that have been sold.
""",
    'data': [  'security/ir.model.access.csv',
        'views/consignment_invoicing_view.xml',
        'data/consignment_sequence.xml',
        'views/sale_order_product_customer_view.xml',
      
      
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
