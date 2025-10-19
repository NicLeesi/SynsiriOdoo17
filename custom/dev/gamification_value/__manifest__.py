# -*- coding: utf-8 -*-
#############################################################################
#
#    NicLee HardDevelop.

############################################################################.
{
    'name': 'Gamification Value',
    'version': '17.0.1.0.0',
    'category': 'Gamification',
    'summary': 'Extension gamification module for update current value for goals',
    'description': 'The module is designed for easy manualy update current state and '
                   'value of employee goal. It enables '
                   'maneger to manually update current value for all individual goal.',
    'author': "Nic Leehard",
    'company': 'Nic Leehard',
    'technical_name': 'gamification_value',
    'maintainer': 'Nic Leehard',
    'website': '',
    'depends': ['base_setup','hr','gamification'],
    'assets': {
        'web.assets_backend': [
            '/gamification_value/static/src/css/karma_style.css',
        ],
    },
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/gamification_views.xml',
        'views/gamification_menu.xml',
        'views/hr_employee_view.xml',
        'views/hr_employee_tree_karma_view.xml',
        'views/gamification_karma_budget_view.xml',
        'views/gamification_goal_views.xml',
        'views/gamification_goal_definition_views.xml',
    ],
    'icon': '/gamification_value/static/description/icon.png',
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
