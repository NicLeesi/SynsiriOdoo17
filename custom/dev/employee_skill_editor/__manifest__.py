# -*- coding: utf-8 -*-
#############################################################################
#
#    NicLee HardDevelop.

############################################################################.
{
    'name': 'Employee Skill Editor',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Editable interface for managing employee skill levels',
    'description': """
Allows administrators to edit employee skills, including level progress, from a dedicated menu.
""",
    'author': 'Your Company Name',
    'depends': ['hr_skills'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_skill_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

