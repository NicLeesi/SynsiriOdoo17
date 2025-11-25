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
from pytz import timezone
from datetime import datetime, timedelta
from odoo import fields, models, api
from odoo.addons.resource.models.utils import Intervals

from odoo.exceptions import AccessError

class HrAttendance(models.Model):
    """Inherit the module to add fields and methods"""
    _inherit = 'hr.attendance'

    days_work_include_late = fields.Float(
        string="Days Work (with Late)",
        compute="_compute_days_work",
        store=True  # Must be True for showing in tree/list views
    )

    late_check_in = fields.Integer(
        string="Late Check-in(Minutes)", compute="_compute_late_check_in",store=True,
        help="This indicates the duration of the employee's tardiness.")

    late_check_in_afternoon = fields.Integer(
        string="Late Afternoon Check-in(Minutes)", compute="_compute_late_check_in_afternoon",store=True,
        help="This indicates the duration of the employee's tardiness.")

    check_in_hour = fields.Float(
        string="Check-In Hour",
        compute='_compute_check_in_hour',
        store=True,
    )

    def action_recompute_days_work(self):
        """Recompute days_work_include_late (Admin only)"""
        # CHECK PERMISSION FIRST
        if not self.env.user.has_group('base.group_system'):
            raise AccessError('Only administrators can recompute attendance data.')

        if not self:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning',
                    'message': 'Please select at least one record',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # Recompute
        for rec in self:
            rec._compute_days_work()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'Recomputed days_work_include_late for {len(self)} record(s)',
                'type': 'success',
                'sticky': False,
            }
        }

    @api.depends('check_in')
    def _compute_check_in_hour(self):
        for record in self:
            if record.check_in:
                # Convert to float hours (e.g., 8:30 = 8.5)
                record.check_in_hour = record.check_in.hour + record.check_in.minute / 60.0
            else:
                record.check_in_hour = 0.0

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_out and attendance.check_in and attendance.employee_id:
                calendar = attendance._get_employee_calendar()
                resource = attendance.employee_id.resource_id
                tz = timezone(calendar.tz)
                check_in_tz = attendance.check_in.astimezone(tz)
                check_out_tz = attendance.check_out.astimezone(tz)
                for rec in self:
                    if rec.employee_id.contract_id:
                        for schedule in rec.sudo().employee_id.contract_id.resource_calendar_id.sudo().attendance_ids:
                            if (schedule.dayofweek == str(
                                    rec.sudo().check_in.weekday()) and
                                    schedule.day_period == 'afternoon'):

                                hour_to_time = datetime.strptime(
                                                '{0:02.0f}:{1:02.0f}'.format(*divmod(
                                                schedule.hour_to * 60, 60)), "%H:%M").time()

                                hour_to_datetime = tz.localize(datetime.combine(check_in_tz.date(), hour_to_time))

                                if check_out_tz > hour_to_datetime:
                                    check_out_tz = hour_to_datetime
                lunch_intervals = calendar._attendance_intervals_batch(
                    check_in_tz, check_out_tz, resource, lunch=True)
                attendance_intervals = Intervals([(check_in_tz, check_out_tz, attendance)]) - lunch_intervals[
                    resource.id]
                delta = sum((i[1] - i[0]).total_seconds() for i in attendance_intervals)
                attendance.worked_hours = delta / 3600.0
            else:
                attendance.worked_hours = False

    @api.depends('check_in', 'check_out')
    def _compute_days_work(self):
        for rec in self:
            rec.days_work_include_late = 0.0  # Always reset first

            if rec.employee_id and rec.employee_id.contract_id:
                contract = rec.employee_id.contract_id
                resource_calendar = contract.resource_calendar_id

                if resource_calendar:
                    average_work_day = resource_calendar.hours_per_day
                    rec_work_hours = rec.worked_hours
                    days_work_total = rec_work_hours / average_work_day
                    day_work_ratio_config = float(
                        self.env['ir.config_parameter'].sudo().get_param('day_work_count_ratio'))

                    if days_work_total < 0.5 * day_work_ratio_config:
                        rec.days_work_include_late = 0
                    elif 0.5 * day_work_ratio_config <= days_work_total <= 1 * day_work_ratio_config:
                        rec.days_work_include_late = 0.5
                    else:
                        rec.days_work_include_late = 1

    @api.depends('worked_hours', 'employee_id.contract_id.resource_calendar_id.hours_per_day')
    def _compute_late_check_in(self):
        for rec in self:
            rec.late_check_in = 0.0
            day_off_morning_check_in = True

            dt = rec.check_in
            if not dt:
                continue

            # Localize to user timezone
            user_tz = pytz.timezone(self.env.user.tz or 'UTC')
            dt_local = pytz.UTC.localize(dt).astimezone(user_tz)
            check_in_date = dt_local.date()

            # Look for a LateCheckInSlot for the check-in day
            slot = self.env['late.check.in.slot'].search([
                ('check_in_change', '>=', datetime.combine(check_in_date, datetime.min.time())),
                ('check_in_change', '<=', datetime.combine(check_in_date, datetime.max.time())),
            ], limit=1)

            grace_minutes = int(self.env['ir.config_parameter'].sudo().get_param('late_check_in_after') or 10)
            grace_delta = timedelta(minutes=grace_minutes)
            max_allowed_late = float(
                self.env['ir.config_parameter'].sudo().get_param('late_check_in_not_count_after') or 9999)

            if slot:
                # Use the check_in_change as the expected check-in time
                expected_dt = slot.check_in_change.astimezone(user_tz)
                expected_time = timedelta(hours=expected_dt.hour, minutes=expected_dt.minute)
                actual_time = timedelta(hours=dt_local.hour, minutes=dt_local.minute)

                if actual_time > expected_time + grace_delta:
                    late_minutes = (actual_time - (expected_time + grace_delta)).total_seconds() / 60
                    rec.late_check_in = late_minutes
                    if late_minutes >= max_allowed_late:
                        rec.late_check_in = 0
                        if rec.days_work_include_late == 1:
                            rec.days_work_include_late -= 0.5
                continue  # Skip rest of calendar logic if a slot is found

            # Normal calendar-based check-in logic
            if rec.employee_id.contract_id:
                calendar = rec.employee_id.contract_id.resource_calendar_id
                for schedule in calendar.sudo().attendance_ids:
                    if schedule.dayofweek == str(dt_local.weekday()) and schedule.day_period == 'morning':
                        day_off_morning_check_in = False
                        scheduled_time = timedelta(
                            hours=int(schedule.hour_from),
                            minutes=int((schedule.hour_from % 1) * 60)
                        )
                        actual_time = timedelta(hours=dt_local.hour, minutes=dt_local.minute)

                        if actual_time > scheduled_time + grace_delta:
                            late_minutes = (actual_time - (scheduled_time + grace_delta)).total_seconds() / 60
                            rec.late_check_in = late_minutes
                            if late_minutes >= max_allowed_late:
                                rec.late_check_in = 0
                                if rec.days_work_include_late == 1:
                                    rec.days_work_include_late -= 0.5

            if day_off_morning_check_in:
                # Use day_off_start_morning config instead
                day_off_hour = float(self.env['ir.config_parameter'].sudo().get_param('day_off_start_morning') or 8.0)
                start_td = timedelta(hours=int(day_off_hour), minutes=int((day_off_hour % 1) * 60))
                actual_td = timedelta(hours=dt_local.hour, minutes=dt_local.minute)

                if actual_td > start_td + grace_delta:
                    late_minutes = (actual_td - (start_td + grace_delta)).total_seconds() / 60
                    rec.late_check_in = late_minutes
                    if late_minutes >= max_allowed_late:
                        rec.late_check_in = 0
                        if rec.days_work_include_late == 1:
                            rec.days_work_include_late -= 0.5


    def late_check_in_records(self):
        """Function creates records in late.check.in model for the employees
        who were late"""
        max_limit = int(self.env['ir.config_parameter'].sudo().get_param(
            'maximum_minutes')) or 0

        for rec in self.sudo().search(
                [('id', 'not in', self.env['late.check.in'].sudo().search(
                    []).attendance_id.ids)]):
            late_check_in = rec.sudo().late_check_in or 0
            late_check_in_afternoon = rec.sudo().late_check_in_afternoon or 0
            total_late_minutes = late_check_in + late_check_in_afternoon

            if total_late_minutes and total_late_minutes < max_limit:

                late_check_in_record = self.env['late.check.in'].sudo().search(
                    [('attendance_id', '=', rec.id)], limit=1)
                if late_check_in_record:
                    # Update existing late check-in record
                    late_check_in_record.write({
                        'late_minutes': total_late_minutes,
                        'date': rec.check_in.date(),
                    })

                else:
                    # Create a new late check-in record
                    self.env['late.check.in'].sudo().create({
                        'employee_id': rec.employee_id.id,
                        'late_minutes': total_late_minutes,
                        'date': rec.check_in.date(),
                        'attendance_id': rec.id,
                    })
        # Identify and delete mismatched late.check.in records
        all_attendance_ids = self.sudo().search([]).ids
        all_late_check_in_records = self.env['late.check.in'].sudo().search([])

        for late_check_in_record in all_late_check_in_records:
            if late_check_in_record.attendance_id.id not in all_attendance_ids:
                late_check_in_record.unlink()
            else:
                corresponding_attendance = self.sudo().browse(late_check_in_record.attendance_id.id)
                late_check_in_total = (corresponding_attendance.late_check_in or 0) + (
                        corresponding_attendance.late_check_in_afternoon or 0)
                if (late_check_in_total != late_check_in_record.late_minutes or
                        corresponding_attendance.check_in.date() != late_check_in_record.date):
                    late_check_in_record.unlink()


    @api.depends('check_in', 'check_out', 'employee_id', 'employee_id.contract_id')
    def _compute_late_check_in_afternoon(self):
        for rec in self:
            rec.late_check_in_afternoon = 0.0

            if not rec.employee_id or not rec.employee_id.contract_id or not rec.check_in:
                continue

            # Get timezone
            tz_name = self.env.user.tz or 'UTC'
            if tz_name not in pytz.all_timezones:
                tz_name = 'UTC'

            old_tz = pytz.timezone('UTC')
            new_tz = pytz.timezone(tz_name)

            # Convert check-in to local timezone
            dt = rec.check_in
            if not dt.tzinfo:
                dt = old_tz.localize(dt)
            dt_local = dt.astimezone(new_tz)

            # Get morning checkout record (pass rec.id to exclude it)
            morning_checkout = self._get_morning_checkout(rec.employee_id, rec.check_in, rec.id)
            if not morning_checkout:
                continue

            # Convert morning checkout to local timezone
            morning_checkout_dt = morning_checkout.check_out
            if not morning_checkout_dt.tzinfo:
                morning_checkout_dt = old_tz.localize(morning_checkout_dt)
            morning_checkout_local = morning_checkout_dt.astimezone(new_tz)

            # Get configuration parameters
            break_time_param = self.env['ir.config_parameter'].sudo().get_param('Lunch_break_time')
            if not break_time_param:
                continue

            break_minutes = int(break_time_param)

            minutes_after_param = self.env['ir.config_parameter'].sudo().get_param('late_check_in_after')
            grace_minutes = int(minutes_after_param) if minutes_after_param else 10

            # Expected afternoon check-in time
            expected_checkin_dt = morning_checkout_local + timedelta(minutes=break_minutes + grace_minutes)

            # Calculate if late
            if dt_local > expected_checkin_dt:
                late_timedelta = dt_local - expected_checkin_dt
                late_minutes = late_timedelta.total_seconds() / 60
                rec.late_check_in_afternoon = late_minutes

                # Check maximum late time
                max_late_param = self.env['ir.config_parameter'].sudo().get_param('late_check_in_not_count_after')
                max_late = float(max_late_param) if max_late_param else 240

                if rec.late_check_in_afternoon >= max_late:
                    rec.late_check_in_afternoon = 0
                    if rec.days_work_include_late > 0:
                        rec.days_work_include_late -= 0.5

    def _get_morning_checkout(self, employee, check_in_datetime, current_record_id=False):
        """Retrieve the morning check-out record for the same day as the given check-in datetime."""

        tz_name = self.env.user.tz or 'UTC'
        if tz_name not in pytz.all_timezones:
            tz_name = 'UTC'

        old_tz = pytz.timezone('UTC')
        new_tz = pytz.timezone(tz_name)

        # Localize if naive
        if not check_in_datetime.tzinfo:
            check_in_datetime_utc = old_tz.localize(check_in_datetime)
        else:
            check_in_datetime_utc = check_in_datetime

        # Convert to local timezone
        local_dt = check_in_datetime_utc.astimezone(new_tz)

        # Start of day in local timezone
        start_of_day_local = local_dt.replace(hour=0, minute=0, second=0, microsecond=0)

        # Convert start of day back to UTC
        start_of_day_utc = new_tz.localize(start_of_day_local.replace(tzinfo=None)).astimezone(old_tz).replace(
            tzinfo=None)

        # Build search domain
        domain = [
            ('employee_id', '=', employee.id),
            ('check_out', '!=', False),
            ('check_out', '>=', start_of_day_utc),
            ('check_out', '<', check_in_datetime),
        ]

        # Exclude current record if provided
        if current_record_id:
            domain.append(('id', '!=', current_record_id))

        # Search morning checkout
        morning_checkout = self.env['hr.attendance'].search(domain, order='check_out desc', limit=1)

        return morning_checkout
