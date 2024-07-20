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
from odoo import api, fields, models
from datetime import datetime


class PayslipLateDiscipline(models.Model):
    """Inherit the model to add fields and functions"""
    _inherit = 'hr.payslip'

    # Field used for writing attendance record in the payslip input
    discipline_ids = fields.Many2many(
        'disciplinary.action', string='discipline',
        help='Discipline records of the employee')

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        print("sec extension called")
        """Function used for writing late check-in and days work records in the payslip input
         tree."""
        res = super(PayslipLateDiscipline, self).get_inputs(contracts, date_from, date_to)

        discipline_id = self.env['disciplinary.action'].search(
            [('employee_name', '=', self.employee_id.id),
             ('state', '=', 'action'),
             ('activate_date', '<=', self.date_to), ('activate_date', '>=', self.date_from)])
        if discipline_id:
            self.discipline_ids = discipline_id
            for discipline in discipline_id:
                discipline_type = discipline.action
                input_data = {
                    'name': f'Discipline: {discipline_type.name} ',
                    'code': discipline_type.code,
                    'amount': sum(discipline_type.mapped('punishment')),
                    'contract_id': self.contract_id.id,
                }
                res.append(input_data)
        print(f"second extension {res}")

        return res