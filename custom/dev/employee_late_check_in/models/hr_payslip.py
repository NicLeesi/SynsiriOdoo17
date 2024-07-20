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


class PayslipLateCheckIn(models.Model):
    """Inherit the model to add fields and functions"""
    _inherit = 'hr.payslip'

    # Field used for writing attendance record in the payslip input
    attendance_ids = fields.Many2many(
        'hr.attendance', string='Attendance',
        help='Attendance records of the employee')

    late_check_in_ids = fields.Many2many(
        'late.check.in', string='Late Check-in',
        help='Late check-in records of the employee')

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        """Function used for writing late check-in and days work records in the payslip input
         tree."""
        res = super(PayslipLateCheckIn, self).get_inputs(contracts,date_from, date_to)
        # Convert date_from and date_to to datetime objects
        if isinstance(date_from, datetime):
            from_datetime = date_from
        else:
            from_datetime = datetime.combine(date_from, datetime.min.time())

        if isinstance(date_to, datetime):
            to_datetime = date_to
        else:
            to_datetime = datetime.combine(date_to, datetime.max.time())

        late_check_in_type = self.env.ref(
            'employee_late_check_in.late_check_in')
        late_check_in_id = self.env['late.check.in'].search(
            [('employee_id', '=', self.employee_id.id),
             ('date', '<=', self.date_to), ('date', '>=', self.date_from),
             ('state', '=', 'approved')])
        if late_check_in_id:
            self.late_check_in_ids = late_check_in_id
            input_data = {
                'name': late_check_in_type.name,
                'code': late_check_in_type.code,
                'amount': sum(late_check_in_id.mapped('penalty_amount')),
                'contract_id': self.contract_id.id,
            }
            res.append(input_data)

        # attendance_type = self.env.ref(
        #     'employee_late_check_in.hr_attendance')
        attendance_id = self.env['hr.attendance'].search(
            [('employee_id', '=', self.employee_id.id),
             ('check_in', '<=', self.date_to), ('check_in', '>=', self.date_from)])
        if attendance_id:
            self.attendance_ids = attendance_id
            input_data = {
                'name': "Total Days Work",
                'code': "DW",
                'amount': sum(attendance_id.mapped('days_work_include_late')),
                'contract_id': self.contract_id.id,
            }
            res.append(input_data)

        if attendance_id:

            calendar = self.employee_id
            leave_dates = calendar.list_leave_dates(from_datetime, to_datetime)
            leave_dates_list = leave_dates
            print(leave_dates_list)
            attendance_ids_leave_filtered = attendance_id.filtered(
                lambda att: (att.check_in.date(), False) in leave_dates_list and att.days_work_include_late != 0
            )

            attendance_ids_sick_filtered = attendance_id.filtered(
                lambda att: (att.check_in.date(), 'SICK') in leave_dates_list and att.days_work_include_late != 0
            )

            # get weekend attendance
            from_datetime = fields.Datetime.from_string(date_from)
            to_datetime = fields.Datetime.from_string(date_to)
            # Get weekend dates
            weekend_dates = calendar.get_weekend_dates(from_datetime, to_datetime)
            # Search for attendance records
            attendance_ids = self.env['hr.attendance'].search(
                [('employee_id', '=', self.employee_id.id),
                 ('check_in', '>=', date_from), ('check_in', '<=', date_to)]
            )
            # Filter the attendance records
            attendance_ids_weekend_filtered = attendance_ids.filtered(
                lambda att: att.check_in.date() in weekend_dates and att.days_work_include_late != 0
            )

            if attendance_ids_leave_filtered:
                self.attendance_ids = attendance_ids_leave_filtered
                input_data = {
                    'name': "Time off Days Work",
                    'code': "ADW",
                    'amount': sum(attendance_ids_leave_filtered.mapped('days_work_include_late')),
                    'contract_id': self.contract_id.id,
                }
                res.append(input_data)

            if attendance_ids_sick_filtered:
                self.attendance_ids = attendance_ids_sick_filtered
                input_data = {
                    'name': "Sick Days Work",
                    'code': "SDW",
                    'amount': sum(attendance_ids_sick_filtered.mapped('days_work_include_late')),
                    'contract_id': self.contract_id.id,
                }
                res.append(input_data)

            if attendance_ids_weekend_filtered:
                input_data = {
                    'name': "Weekend Work",
                    'code': 'WDW',
                    'amount': sum(attendance_ids_weekend_filtered.mapped('days_work_include_late')),
                    'contract_id': self.contract_id.id,
                }
                res.append(input_data)

        return res


    def action_payslip_done(self):
        """Function used for marking deducted Late check-in request."""
        for rec in self.late_check_in_ids:
            rec.state = 'deducted'
        return super(PayslipLateCheckIn, self).action_payslip_done()
