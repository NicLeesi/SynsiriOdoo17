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
import pytz
from datetime import datetime, timedelta
from odoo import fields, models, api
import logging


class HrAttendance(models.Model):
    """Inherit the module to add fields and methods"""
    _inherit = 'hr.attendance'

    days_work_include_late = fields.Float(
        string="Days work(late include) ", compute="_compute_days_work",
        help="This indicates the duration of the employee's tardiness.")

    late_check_in = fields.Integer(
        string="Late Check-in(Minutes)", compute="_compute_late_check_in",
        help="This indicates the duration of the employee's tardiness.")

    late_check_in_afternoon = fields.Integer(
        string="Late Afternoon Check-in(Minutes)", compute="_compute_late_check_in_afternoon",
        help="This indicates the duration of the employee's tardiness.")

    def _compute_days_work(self):
        """Calculate days of work for each record in current model"""
        for rec in self:
            rec.days_work_include_late = 0.0
            if rec.employee_id and rec.employee_id.contract_id:
                contract = rec.employee_id.contract_id
                resource_calendar = contract.resource_calendar_id
                if resource_calendar:
                    average_work_day = resource_calendar.hours_per_day
                    rec_work_hours = rec.worked_hours
                    rec_late_check_in = rec.late_check_in / 60
                    # rec_late_check_in_afternoon = rec.late_check_in_afternoon / 60

                    rec.days_work_include_late = (rec_work_hours + rec_late_check_in) / average_work_day
                    print(rec.days_work_include_late)
                    if rec.days_work_include_late < ( 1 / 2 ) * 0.75:
                        rec.days_work_include_late = 0
                        if rec.late_check_in >= float(self.env['ir.config_parameter'].sudo().get_param(
                                'late_check_in_not_count_after')):
                            rec.days_work_include_late = 0
                    else:
                        if rec.days_work_include_late >= ( 1 / 2 ) * 0.75 and rec.days_work_include_late <= 1 * 0.75:
                            rec.days_work_include_late = 0.5

                        elif rec.days_work_include_late <= 1 * 0.75 and rec.days_work_include_late >= ( 1 / 2 ) * 0.75:
                            rec.days_work_include_late = 1
    def _compute_late_check_in(self):
        """Calculate late check-in minutes for each record in the current Odoo
        model.This method iterates through the records and calculates late
        check-in minutes based on the employee's contract schedule.The
        calculation takes into account the employee's time zone, scheduled
        check-in time, and the actual check-in time."""
        for rec in self:
            rec.late_check_in = 0.0
            day_off_morning_check_in = True
            if rec.employee_id.contract_id:
                for schedule in rec.sudo().employee_id.contract_id.resource_calendar_id.sudo().attendance_ids:
                    if (schedule.dayofweek == str(
                            rec.sudo().check_in.weekday()) and
                            schedule.day_period == 'morning'):
                        day_off_morning_check_in = False
                        dt = rec.check_in
                        if self.env.user.tz in pytz.all_timezones:
                            old_tz = pytz.timezone('UTC')
                            new_tz = pytz.timezone(self.env.user.tz)
                            dt = old_tz.localize(dt).astimezone(new_tz)
                        str_time = dt.strftime("%H:%M")
                        check_in_date = datetime.strptime(
                            str_time, "%H:%M").time()
                        start_date = datetime.strptime(
                            '{0:02.0f}:{1:02.0f}'.format(*divmod(
                                schedule.hour_from * 60, 60)), "%H:%M").time()
                        check_in = timedelta(hours=check_in_date.hour,
                                             minutes=check_in_date.minute)
                        start_date = timedelta(hours=start_date.hour,
                                               minutes=start_date.minute)
                        if check_in > start_date:
                            final = check_in - start_date
                            rec.late_check_in = final.total_seconds() / 60

                            if rec.late_check_in >= float(self.env['ir.config_parameter'].sudo().get_param(
                                    'late_check_in_not_count_after')):
                                rec.late_check_in = 0
                if day_off_morning_check_in:
                        dt = rec.check_in
                        if self.env.user.tz in pytz.all_timezones:
                            old_tz = pytz.timezone('UTC')
                            new_tz = pytz.timezone(self.env.user.tz)
                            dt = old_tz.localize(dt).astimezone(new_tz)
                        str_time = dt.strftime("%H:%M")
                        check_in_date = datetime.strptime(
                            str_time, "%H:%M").time()
                        start_date = datetime.strptime(
                            '{0:02.0f}:{1:02.0f}'.format(*divmod(float(
                                self.env['ir.config_parameter'].sudo().get_param(
                                    'day_off_start_morning')) * 60, 60)), "%H:%M").time()
                        check_in = timedelta(hours=check_in_date.hour,
                                             minutes=check_in_date.minute)
                        start_date = timedelta(hours=start_date.hour,
                                               minutes=start_date.minute)
                        if check_in > start_date:
                            final = check_in - start_date
                            rec.late_check_in = final.total_seconds() / 60

                            if rec.late_check_in >= float(self.env['ir.config_parameter'].sudo().get_param(
                                    'late_check_in_not_count_after')):
                                rec.late_check_in = 0


    def late_check_in_records(self):
        """Function creates records in late.check.in model for the employees
        who were late"""
        minutes_after = int(self.env['ir.config_parameter'].sudo().get_param(
            'late_check_in_after')) or 10
        max_limit = int(self.env['ir.config_parameter'].sudo().get_param(
            'maximum_minutes')) or 0
        for rec in self.sudo().search(
                [('id', 'not in', self.env['late.check.in'].sudo().search(
                    []).attendance_id.ids)]):
            late_check_in = rec.sudo().late_check_in
            if rec.late_check_in > minutes_after and late_check_in > minutes_after and late_check_in < max_limit:
                self.env['late.check.in'].sudo().create({
                    'employee_id': rec.employee_id.id,
                    'late_minutes': late_check_in,
                    'date': rec.check_in.date(),
                    'attendance_id': rec.id,
                })

    def _compute_late_check_in_afternoon(self):
        """Calculate late check-in for (afternoon session) minutes for each record in the current Odoo
        model.This method iterates through the records and calculates late
        check-in minutes based on the employee's contract schedule.The
        calculation takes into account the employee's time zone, scheduled
        check-in time, and the actual check-in time."""
        for rec in self:
            rec.late_check_in_afternoon = 0.0
            if rec.employee_id.contract_id:
                dt = rec.check_in
                if self.env.user.tz in pytz.all_timezones:
                    old_tz = pytz.timezone('UTC')
                    new_tz = pytz.timezone(self.env.user.tz)
                    dt = old_tz.localize(dt).astimezone(new_tz)
                str_time = dt.strftime("%H:%M")
                check_in_date = datetime.strptime(
                    str_time, "%H:%M").time()
                morning_checkout = self._get_morning_checkout(rec.employee_id, rec.check_in)
                if morning_checkout:
                    morning_checkout_time = morning_checkout.check_out
                    morning_checkout_time = old_tz.localize(morning_checkout_time).astimezone(
                        new_tz)
                    morning_checkout_str_time = morning_checkout_time.strftime("%H:%M")
                    morning_checkout_time = datetime.strptime(morning_checkout_str_time,
                                                              "%H:%M").time()
                    morning_checkout_timedelta = timedelta(hours=morning_checkout_time.hour,
                                                           minutes=morning_checkout_time.minute)

                    break_time = int(self.env['ir.config_parameter'].sudo().get_param(
                                'Lunch_break_time'))
                    check_in = timedelta(hours=check_in_date.hour,
                                         minutes=check_in_date.minute)
                    break_time = timedelta(minutes=break_time)

                    if check_in > morning_checkout_timedelta + break_time :
                        final = check_in - (morning_checkout_timedelta + break_time)
                        rec.late_check_in_afternoon = final.total_seconds() / 60

    def _get_morning_checkout(self, employee, check_in_datetime):
        """Retrieve the morning check-out record for the same day as the given check-in datetime."""
        start_of_day = check_in_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
        noon = start_of_day + timedelta(hours=23)

        return self.env['hr.attendance'].search([
            ('employee_id', '=', employee.id),
            ('check_out', '>=', start_of_day),
            ('check_out', '<', check_in_datetime)
        ], limit=1)

