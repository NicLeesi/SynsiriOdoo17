# -*- coding: utf-8 -*-
#############################################################################
#
#    NicLee HardDevelop.

############################################################################.
{
    'name': 'Gamification Update value',
    'version': '17.0.1.0.0',
    'category': 'Gamification',
    'summary': 'Extension gamification module for update current value for goals',
    'description': 'The module is designed for easy manualy update current state and '
                   'value of employee goal. It enables '
                   'maneger to manually update current value for all individual goal.',
    'author': "Nic Leehard",
    'company': 'Nic Leehard',
    'maintainer': 'Nic Leehard',
    'website': '',
    'depends': ['gamification'],
    'data': [
        'views/gamification_views.xml',
        'views/gamification_menu.xml',
        'security/ir.model.access.csv',
        'views/gamification_goal_views.xml',
        'views/gamification_goal_definition_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
