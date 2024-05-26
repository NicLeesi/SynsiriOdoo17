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


class HrAttendance(models.Model):
    """Inherit the module to add fields and methods"""
    _inherit = 'hr.attendance'

    days_work_include_late = fields.Float(
        string="Days work(late include) ", compute="_compute_Days_work",
        help="This indicates the duration of the employee's tardiness.")

    late_check_in = fields.Integer(
        string="Late Check-in(Minutes)", compute="_compute_late_check_in",
        help="This indicates the duration of the employee's tardiness.")

    late_check_in_afternoon = fields.Integer(
        string="Late Afternoon Check-in(Minutes)", compute="_compute_late_check_in_afternoon",
        help="This indicates the duration of the employee's tardiness.")

    def _compute_Days_work(self):
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
                    rec_late_check_in_afternoon = rec.late_check_in_afternoon / 60

                    rec.days_work_include_late = (rec_work_hours + rec_late_check_in + rec_late_check_in_afternoon) / average_work_day


    # def _compute_late_check_in(self):
    #     """Calculate late check-in minutes for each record in the current Odoo
    #     model.This method iterates through the records and calculates late
    #     check-in minutes based on the employee's contract schedule.The
    #     calculation takes into account the employee's time zone, scheduled
    #     check-in time, and the actual check-in time."""
    #     for rec in self:
    #         rec.late_check_in = 0.0
    #         if rec.employee_id.contract_id:
    #             for schedule in rec.sudo().employee_id.contract_id.resource_calendar_id.sudo().attendance_ids:
    #                 if (schedule.dayofweek == str(
    #                         rec.sudo().check_in.weekday()) and
    #                         schedule.day_period == 'morning'):
    #                     dt = rec.check_in
    #                     if self.env.user.tz in pytz.all_timezones:
    #                         old_tz = pytz.timezone('UTC')
    #                         new_tz = pytz.timezone(self.env.user.tz)
    #                         dt = old_tz.localize(dt).astimezone(new_tz)
    #                     str_time = dt.strftime("%H:%M")
    #                     check_in_date = datetime.strptime(
    #                         str_time, "%H:%M").time()
    #                     start_date = datetime.strptime(
    #                         '{0:02.0f}:{1:02.0f}'.format(*divmod(
    #                             schedule.hour_from * 60, 60)), "%H:%M").time()
    #                     check_in = timedelta(hours=check_in_date.hour,
    #                                          minutes=check_in_date.minute)
    #                     start_date = timedelta(hours=start_date.hour,
    #                                            minutes=start_date.minute)
    #                     if check_in > start_date:
    #                         final = check_in - start_date
    #                         rec.late_check_in = final.total_seconds() / 60
    #
    #                         if rec.late_check_in >= float(self.env['ir.config_parameter'].sudo().get_param(
    #                                 'late_check_in_not_count_after')):
    #                             rec.late_check_in = 0
    #                 else:
    #                     dt = rec.check_in
    #                     if self.env.user.tz in pytz.all_timezones:
    #                         old_tz = pytz.timezone('UTC')
    #                         new_tz = pytz.timezone(self.env.user.tz)
    #                         dt = old_tz.localize(dt).astimezone(new_tz)
    #                     str_time = dt.strftime("%H:%M")
    #                     check_in_date = datetime.strptime(
    #                         str_time, "%H:%M").time()
    #                     start_date = datetime.strptime(
    #                         '{0:02.0f}:{1:02.0f}'.format(*divmod(float(
    #                             self.env['ir.config_parameter'].sudo().get_param(
    #                                 'day_off_start_morning')) * 60, 60)), "%H:%M").time()
    #                     check_in = timedelta(hours=check_in_date.hour,
    #                                          minutes=check_in_date.minute)
    #                     start_date = timedelta(hours=start_date.hour,
    #                                            minutes=start_date.minute)
    #                     if check_in > start_date:
    #                         final = check_in - start_date
    #                         rec.late_check_in = final.total_seconds() / 60
    #
    #                         if rec.late_check_in >= float(self.env['ir.config_parameter'].sudo().get_param(
    #                                 'late_check_in_not_count_after')):
    #                             rec.late_check_in = 0

    def _compute_late_check_in(self):
        """Calculate late check-in minutes for each record in the current Odoo model."""
        for rec in self:
            rec.late_check_in = 0.0
            contract = rec.employee_id.contract_id
            if contract:
                check_in_time = self._convert_to_user_timezone(rec.check_in)
                for schedule in contract.resource_calendar_id.attendance_ids:
                    if schedule.dayofweek == str(check_in_time.weekday()) and schedule.day_period == 'morning':
                        scheduled_time = self._time_from_float(schedule.hour_from)
                        rec.late_check_in = self._calculate_late_minutes(check_in_time, scheduled_time)
                    else:
                        day_off_start = float(self.env['ir.config_parameter'].sudo().get_param('day_off_start_morning'))
                        scheduled_time = self._time_from_float(day_off_start)
                        rec.late_check_in = self._calculate_late_minutes(check_in_time, scheduled_time)

                    if rec.late_check_in >= float(
                            self.env['ir.config_parameter'].sudo().get_param('late_check_in_not_count_after')):
                        rec.late_check_in = 0

    def _compute_late_check_in_afternoon(self):
        """Calculate late check-in minutes for each record in the current Odoo model."""
        for rec in self:
            rec.late_check_in_afternoon = 0.0
            contract = rec.employee_id.contract_id
            if contract:
                check_in_time = self._convert_to_user_timezone(rec.check_in)
                for schedule in contract.resource_calendar_id.attendance_ids:
                    if schedule.dayofweek == str(check_in_time.weekday()) and schedule.day_period == 'afternoon':
                        scheduled_time = self._time_from_float(schedule.hour_from)
                        rec.late_check_in_afternoon = self._calculate_late_minutes(check_in_time, scheduled_time)
                    else:
                        day_off_start = float(self.env['ir.config_parameter'].sudo().get_param('day_off_start_afternoon'))
                        scheduled_time = self._time_from_float(day_off_start)
                        rec.late_check_in_afternoon = self._calculate_late_minutes(check_in_time, scheduled_time)

                    if rec.late_check_in >= float(
                            self.env['ir.config_parameter'].sudo().get_param('late_check_in_not_count_after')):
                        rec.late_check_in_afternoon = 0

    def _convert_to_user_timezone(self, dt):
        """Convert a datetime object to the user's timezone."""
        old_tz = pytz.timezone('UTC')
        new_tz = pytz.timezone(self.env.user.tz) if self.env.user.tz in pytz.all_timezones else old_tz
        return old_tz.localize(dt).astimezone(new_tz)

    def _time_from_float(self, time_float):
        """Convert a float representing hours to a time object."""
        hours, minutes = divmod(time_float * 60, 60)
        return timedelta(hours=int(hours), minutes=int(minutes))

    def _calculate_late_minutes(self, check_in_time, scheduled_time):
        """Calculate the number of late minutes."""
        check_in = timedelta(hours=check_in_time.hour, minutes=check_in_time.minute)
        if check_in > scheduled_time:
            return (check_in - scheduled_time).total_seconds() / 60
        return 0.0



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

    # def _compute_late_check_in_afternoon(self):
    #     """Calculate late check-in for (afternoon session) minutes for each record in the current Odoo
    #     model.This method iterates through the records and calculates late
    #     check-in minutes based on the employee's contract schedule.The
    #     calculation takes into account the employee's time zone, scheduled
    #     check-in time, and the actual check-in time."""
    #     for rec in self:
    #         rec.late_check_in_afternoon = 0.0
    #         if rec.employee_id.contract_id:
    #             for schedule in rec.sudo().employee_id.contract_id.resource_calendar_id.sudo().attendance_ids:
    #                 if (schedule.dayofweek == str(
    #                         rec.sudo().check_in.weekday()) and
    #                         schedule.day_period == 'afternoon'):
    #                     dt = rec.check_in
    #                     if self.env.user.tz in pytz.all_timezones:
    #                         old_tz = pytz.timezone('UTC')
    #                         new_tz = pytz.timezone(self.env.user.tz)
    #                         dt = old_tz.localize(dt).astimezone(new_tz)
    #                     str_time = dt.strftime("%H:%M")
    #                     check_in_date = datetime.strptime(
    #                         str_time, "%H:%M").time()
    #                     start_date = datetime.strptime(
    #                         '{0:02.0f}:{1:02.0f}'.format(*divmod(
    #                             schedule.hour_from * 60, 60)), "%H:%M").time()
    #                     check_in = timedelta(hours=check_in_date.hour,
    #                                          minutes=check_in_date.minute)
    #                     start_date = timedelta(hours=start_date.hour,
    #                                            minutes=start_date.minute)
    #                     if check_in > start_date:
    #                         final = check_in - start_date
    #                         rec.late_check_in_afternoon = final.total_seconds() / 60
    #
    #
    #                 else:
    #                     dt = rec.check_in
    #                     if self.env.user.tz in pytz.all_timezones:
    #                         old_tz = pytz.timezone('UTC')
    #                         new_tz = pytz.timezone(self.env.user.tz)
    #                         dt = old_tz.localize(dt).astimezone(new_tz)
    #                     str_time = dt.strftime("%H:%M")
    #                     check_in_date = datetime.strptime(
    #                         str_time, "%H:%M").time()
    #                     start_date = datetime.strptime(
    #                         '{0:02.0f}:{1:02.0f}'.format(*divmod(float(
    #                             self.env['ir.config_parameter'].sudo().get_param(
    #                                 'day_off_start_afternoon')) * 60, 60)), "%H:%M").time()
    #                     check_in = timedelta(hours=check_in_date.hour,
    #                                          minutes=check_in_date.minute)
    #                     start_date = timedelta(hours=start_date.hour,
    #                                            minutes=start_date.minute)
    #                     if check_in > start_date:
    #                         final = check_in - start_date
    #                         rec.late_check_in_afternoon = final.total_seconds() / 60
    #
    #                         if rec.late_check_in >= float(self.env['ir.config_parameter'].sudo().get_param(
    #                                 'late_check_in_not_count_after')):
    #                             rec.late_check_in = 0