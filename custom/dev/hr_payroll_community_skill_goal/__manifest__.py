# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Payroll extend skill and goal variable',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Extention for payslip to compute salary rule using skill and goal variables',
    'description': "For Employee Payslip to call skill and goal variables in salary rule computation by python code",
    'author': 'Nic Lee Hard Develop',
    'maintainer': 'Nic Lee Hard Develop',
    'depends': ['hr_payroll_community'],
    'data': ['security/ir.model.access.csv',
 ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
