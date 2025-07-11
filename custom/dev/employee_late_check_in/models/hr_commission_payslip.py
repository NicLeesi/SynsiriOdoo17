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

from datetime import date, datetime, time
from odoo import api, fields, models, tools, _


class ComPayslipLateCheckIn(models.Model):
    """Inherit the model to add fields and functions"""
    _inherit = 'hr.commission.payslip'
    # _order = 'create_date desc, id desc'

    # Field used for writing attendance record in the payslip input
    attendance_ids = fields.Many2many(
        'hr.attendance', string='Attendance',
        help='Attendance records of the employee')

    late_check_in_ids = fields.Many2many(
        'late.check.in', string='Late Check-in',
        help='Late check-in records of the employee')

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        """Function used for writing late check-in and days work records in the payslip input tree."""
        if not self.employee_id or not date_from or not date_to or not contracts:
            return []

        res = super(ComPayslipLateCheckIn, self).get_inputs(contracts, date_from, date_to)

        from_datetime = date_from if isinstance(date_from, datetime) else datetime.combine(date_from,
                                                                                           datetime.min.time())
        to_datetime = date_to if isinstance(date_to, datetime) else datetime.combine(date_to, datetime.max.time())

        # Get resource calendar from contract
        calendar = contracts[0].resource_calendar_id if contracts[0].resource_calendar_id else self.env[
            'resource.calendar']

        # Defensive: fallback and safety check
        if not calendar or not calendar.ids:
            return res
        calendar = calendar[0]

        # Leave Dates
        try:
            leave_dates = calendar.list_leave_dates(from_datetime, to_datetime)
        except AttributeError:
            leave_dates = []
        leave_dates_list = leave_dates

        # Attendance records
        attendance_id = self.env['hr.attendance'].search([
            ('employee_id', '=', self.employee_id.id),
            ('check_in', '<=', self.date_to),
            ('check_in', '>=', self.date_from)
        ])

        # Filter attendance by leave code
        attendance_ids_leave_filtered = attendance_id.filtered(
            lambda att: (att.check_in.date(), False) in leave_dates_list and att.days_work_include_late != 0
        )
        attendance_ids_sick_filtered = attendance_id.filtered(
            lambda att: (att.check_in.date(), 'SICK') in leave_dates_list and att.days_work_include_late != 0
        )

        # Weekend work filter
        try:
            weekend_dates = calendar.get_weekend_dates(from_datetime, to_datetime)
        except AttributeError:
            weekend_dates = []

        attendance_ids_weekend_filtered = attendance_id.filtered(
            lambda att: att.check_in.date() in weekend_dates and att.days_work_include_late != 0
        )

        # Late Check-In
        late_check_in_type = self.env.ref('employee_late_check_in.late_check_in', raise_if_not_found=False)
        late_check_in_id = self.env['late.check.in'].search([
            ('employee_id', '=', self.employee_id.id),
            ('date', '<=', self.date_to),
            ('date', '>=', self.date_from),
            ('state', '=', 'approved')
        ])
        if late_check_in_type and late_check_in_id:
            self.late_check_in_ids = late_check_in_id
            res.append({
                'name': late_check_in_type.name,
                'code': late_check_in_type.code,
                'amount': sum(late_check_in_id.mapped('penalty_amount')),
                'contract_id': self.contract_id.id,
            })

        # Total Days Work
        if attendance_id:
            self.attendance_ids = attendance_id
            res.append({
                'name': "Total Days Work",
                'code': "DW",
                'amount': sum(attendance_id.mapped('days_work_include_late')),
                'contract_id': self.contract_id.id,
            })

        if attendance_ids_leave_filtered:
            self.attendance_ids = attendance_ids_leave_filtered
            res.append({
                'name': "Time off Days Work",
                'code': "ADW",
                'amount': sum(attendance_ids_leave_filtered.mapped('days_work_include_late')),
                'contract_id': self.contract_id.id,
            })

        if attendance_ids_sick_filtered:
            self.attendance_ids = attendance_ids_sick_filtered
            res.append({
                'name': "Sick Days Work",
                'code': "SDW",
                'amount': sum(attendance_ids_sick_filtered.mapped('days_work_include_late')),
                'contract_id': self.contract_id.id,
            })

        if attendance_ids_weekend_filtered:
            res.append({
                'name': "Weekend Work",
                'code': 'WDW',
                'amount': sum(attendance_ids_weekend_filtered.mapped('days_work_include_late')),
                'contract_id': self.contract_id.id,
            })

        return res

    # # Original code nicky
    # @api.model
    # def get_inputs(self, contracts, date_from, date_to):
    #     """Function used for writing late check-in and days work records in the payslip input
    #      tree."""
    #     res = super(ComPayslipLateCheckIn, self).get_inputs(contracts, date_from, date_to)
    #
    #     attendance_id = self.env['hr.attendance'].search(
    #         [('employee_id', '=', self.employee_id.id),
    #          ('check_in', '<=', self.date_to), ('check_in', '>=', self.date_from)])
    #
    #     # Convert date_from and date_to to datetime objects
    #     if isinstance(date_from, datetime):
    #         from_datetime = date_from
    #     else:
    #         from_datetime = datetime.combine(date_from, datetime.min.time())
    #
    #     if isinstance(date_to, datetime):
    #         to_datetime = date_to
    #     else:
    #         to_datetime = datetime.combine(date_to, datetime.max.time())
    #
    #     calendar = self.employee_id
    #     leave_dates = calendar.list_leave_dates(from_datetime, to_datetime)
    #     leave_dates_list = leave_dates
    #
    #     attendance_ids_leave_filtered = attendance_id.filtered(
    #         lambda att: (att.check_in.date(), False) in leave_dates_list and att.days_work_include_late != 0
    #     )
    #
    #     attendance_ids_sick_filtered = attendance_id.filtered(
    #         lambda att: (att.check_in.date(), 'SICK') in leave_dates_list and att.days_work_include_late != 0
    #     )
    #
    #     # Get weekend attendance
    #     weekend_dates = calendar.get_weekend_dates(from_datetime, to_datetime)
    #
    #     attendance_ids_weekend_filtered = attendance_id.filtered(
    #         lambda att: att.check_in.date() in weekend_dates and att.days_work_include_late != 0
    #     )
    #
    #     late_check_in_type = self.env.ref(
    #         'employee_late_check_in.late_check_in')
    #     late_check_in_id = self.env['late.check.in'].search(
    #         [('employee_id', '=', self.employee_id.id),
    #          ('date', '<=', self.date_to), ('date', '>=', self.date_from),
    #          ('state', '=', 'approved')])
    #     if late_check_in_id:
    #         self.late_check_in_ids = late_check_in_id
    #         input_data = {
    #             'name': late_check_in_type.name,
    #             'code': late_check_in_type.code,
    #             'amount': sum(late_check_in_id.mapped('penalty_amount')),
    #             'contract_id': self.contract_id.id,
    #         }
    #         res.append(input_data)
    #
    #
    #     if attendance_id:
    #         self.attendance_ids = attendance_id
    #         input_data = {
    #             'name': "Total Days Work",
    #             'code': "DW",
    #             'amount': sum(attendance_id.mapped('days_work_include_late')),
    #             'contract_id': self.contract_id.id,
    #         }
    #         res.append(input_data)
    #
    #
    #
    #     if attendance_ids_leave_filtered:
    #         self.attendance_ids = attendance_ids_leave_filtered
    #         input_data = {
    #             'name': "Time off Days Work",
    #             'code': "ADW",
    #             'amount': sum(attendance_ids_leave_filtered.mapped('days_work_include_late')),
    #             'contract_id': self.contract_id.id,
    #         }
    #         res.append(input_data)
    #
    #     if attendance_ids_sick_filtered:
    #         self.attendance_ids = attendance_ids_sick_filtered
    #         input_data = {
    #             'name': "Sick Days Work",
    #             'code': "SDW",
    #             'amount': sum(attendance_ids_sick_filtered.mapped('days_work_include_late')),
    #             'contract_id': self.contract_id.id,
    #         }
    #         res.append(input_data)
    #
    #     if attendance_ids_weekend_filtered:
    #         input_data = {
    #             'name': "Weekend Work",
    #             'code': 'WDW',
    #             'amount': sum(attendance_ids_weekend_filtered.mapped('days_work_include_late')),
    #             'contract_id': self.contract_id.id,
    #         }
    #         res.append(input_data)
    #
    #     return res

