# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohamed Muzammil VP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
############################################################################.
{
    'name': 'Employee Payroll Commission',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Extension Payroll module for managing commission slip'
               'skill and chaleanges of employees and relate to computing commission payslip',
    'description': 'The module is designed for meticulous tracking and '
                   'management of employee commission. It enables '
                   'organizations to assesment skill and set chalenges for compute, '
                   'employee slip.  This module contributes to fostering'
                   ' a learning and efficient work.',
    'author': "Nic Leehard",
    'company': 'Nic Leehard',
    'maintainer': 'Nic Leehard',
    'website': '',
    'depends': ['hr_payroll_community'],
    'data': [
        'wizard/hr_payslips_employees_views.xml',
        'data/salary_rule.xml',
        'views/hr_commission_payslip_views.xml',
        'views/hr_employee_views.xml',
        'security/ir.model.access.csv',
        'views/hr_commission_payslip_line_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_payslip_run_views.xml',
        'data/hr_com_payroll_sequence.xml',



    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
