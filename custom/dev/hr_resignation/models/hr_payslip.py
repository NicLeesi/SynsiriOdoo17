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
    resignation_ids = fields.Many2many(
        'hr.resignation', string='resignation return insurance',
        help='Resignation records of the employee')

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        """Function used for writing return insurance records in the payslip input
         tree."""
        res = super(PayslipLateDiscipline, self).get_inputs(contracts, date_from, date_to)

        resignation_id = self.env['hr.resignation'].search(
            [('employee_id', '=', self.employee_id.id),
             ('state', '=', 'confirm'),
             ('expected_revealing_date', '<=', self.date_to), ('expected_revealing_date', '>=', self.date_from)])
        if resignation_id:
            self.resignation_ids = resignation_id
            for resignation in resignation_id:
                # resignation_type = resignation.confirm
                input_data = {
                    'name': 'Return Insurance',
                    'code': 'RIN',
                    'amount': resignation.return_insurance,
                    'contract_id': self.contract_id.id,
                }
                res.append(input_data)

        return res
