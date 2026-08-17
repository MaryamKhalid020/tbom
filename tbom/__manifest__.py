{
    'name': 'Temporary Business Operations Management (TBOM)',
    'version': '1.1.2',
    'category': 'Operations',
    'summary': 'Manage temporary, time- and location-bound business operations',
    'description': """
Temporary Business Operations Manager (TBOM)

This module manages temporary business operations such as:
- Exhibitions
- Trade fairs
- Seasonal outlets
- Promotional campaigns
- Temporary warehouses
- Field operations

It provides a centralized view of employees, inventory,
equipment, expenses, purchases and budgets associated
with a temporary operation.
    """,
    'author': 'TBOM Development Team',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr',
        'mail',
    ],
    'data': [
        'security/tbom_security.xml',
        'security/ir.model.access.csv',
        'views/temporary_operation_views.xml',
        'views/tbom_resource_views.xml',
        'views/tbom_employee_assignment_views.xml',
        'views/tbom_equipment_views.xml',
        'views/tbom_expense_views.xml',
        'views/tbom_state_history_views.xml',
        'views/tbom_send_message_views.xml',
        'reports/temporary_operation_reports.xml',
    ],
    'installable': True,
    'application': True,
}