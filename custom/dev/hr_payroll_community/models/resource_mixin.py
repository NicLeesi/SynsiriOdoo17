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
from collections import defaultdict
from datetime import timedelta, timezone

from pytz import utc
from dateutil.rrule import rrule, DAILY
from odoo import models, fields
from odoo.tools import float_utils

# This will generate 16th of days
ROUNDING_FACTOR = 16


class ResourceMixin(models.AbstractModel):
    """Inherit resource_mixin for getting Worked Days"""
    _inherit = "resource.mixin"

    def get_work_days_data(self, from_datetime, to_datetime,
                           compute_leaves=True, calendar=None, domain=None):
        """
            By-default the resource calendar is used, but it can be
            changed using the `calendar` argument.

            `domain` is used in order to recognise the leaves to take,
            None means default value ('time_type', '=', 'leave')

            Returns a dict {'days': n, 'hours': h} containing the
            quantity of working time expressed as days and as hours.
        """
        resource = self.resource_id
        calendar = calendar or self.resource_calendar_id
        # naive datetimes are made explicit in UTC
        if not from_datetime.tzinfo:
            from_datetime = from_datetime.replace(tzinfo=utc)
        if not to_datetime.tzinfo:
            to_datetime = to_datetime.replace(tzinfo=utc)
        # total hours per day: retrieve attendances with one extra day margin,
        # in order to compute the total hours on the first and last days
        from_full = from_datetime - timedelta(days=1)
        to_full = to_datetime + timedelta(days=1)
        intervals = calendar._attendance_intervals_batch(from_full, to_full,
                                                         resource)
        day_total = defaultdict(float)
        for start, stop, meta in intervals[resource.id]:
            day_total[start.date()] += (stop - start).total_seconds() / 3600
        # actual hours per day
        if compute_leaves:
            intervals = calendar._work_intervals_batch(from_datetime,
                                                       to_datetime, resource,
                                                       domain)
        else:
            intervals = calendar._attendance_intervals_batch(from_datetime,
                                                             to_datetime,
                                                             resource)
        day_hours = defaultdict(float)
        for start, stop, meta in intervals[resource.id]:
            day_hours[start.date()] += (stop - start).total_seconds() / 3600
        # compute number of days as quarters
        days = sum(
            float_utils.round(ROUNDING_FACTOR * day_hours[day] / day_total[
                day]) / ROUNDING_FACTOR
            for day in day_hours
        )
        return {
            'days': days,
            'hours': sum(day_hours.values()),
        }

    def list_leave_dates(self, from_datetime, to_datetime, calendar=None, domain=None):
        """
            This method returns a list of unique dates for the leaves within
            the given datetime range. By default, the resource calendar is used,
            but it can be changed using the `calendar` argument.

            `domain` is used to filter the leaves, None means default value ('time_type', '=', 'leave').

            Returns a list of unique dates for the leaves in the calendar.
        """
        resource = self.resource_id
        calendar = calendar or self.resource_calendar_id

        # Ensure datetimes are in UTC if naive
        if not from_datetime.tzinfo:
            from_datetime = from_datetime.replace(tzinfo=utc)
        if not to_datetime.tzinfo:
            to_datetime = to_datetime.replace(tzinfo=utc)

        attendances = calendar._attendance_intervals_batch(from_datetime, to_datetime, resource)[resource.id]
        leaves = calendar._leave_intervals_batch(from_datetime, to_datetime, resource, domain)[resource.id]

        leave_dates = set()
        for start, stop, leave in (leaves & attendances):
            code = leave.holiday_id.holiday_status_id.code
            leave_dates.add((start.date(), code))
            leave_dates.add((stop.date(), code))

        return list(leave_dates)

    def get_weekend_dates(self, from_datetime, to_datetime):

        if not from_datetime.tzinfo:
            from_datetime = from_datetime.replace(tzinfo=timezone.utc)
        if not to_datetime.tzinfo:
            to_datetime = to_datetime.replace(tzinfo=timezone.utc)
        calendar = self.resource_calendar_id
        attendances = calendar._attendance_intervals_batch(from_datetime, to_datetime, self.resource_id)[
            self.resource_id.id]

        # Get all weekdays with attendance
        attendance_days = set(attendance[0].weekday() for attendance in attendances)

        # All days of the week (0 is Monday, 6 is Sunday)
        all_days = set(range(7))

        # Weekends are days that are not in attendance_days
        weekend_days = all_days - attendance_days

        # Generate all dates between from_datetime and to_datetime
        dates = rrule(DAILY, from_datetime, until=to_datetime)

        # Filter out the dates that are weekends
        weekend_dates = [dt.date() for dt in dates if dt.weekday() in weekend_days]

        return weekend_dates

    # def get_weekend_attendance(self, date_from, date_to):
    #     # Convert to datetime
    #     from_datetime = fields.Datetime.from_string(date_from)
    #     to_datetime = fields.Datetime.from_string(date_to)
    #
    #     # Get weekend dates
    #     weekend_dates = self.get_weekend_dates(from_datetime, to_datetime)
    #
    #     # Search for attendance records
    #     attendance_ids = self.env['hr.attendance'].search(
    #         [('employee_id', '=', self.employee_id.id),
    #          ('check_in', '>=', date_from), ('check_in', '<=', date_to)]
    #     )
    #
    #     # Filter the attendance records
    #     attendance_ids_filtered = attendance_ids.filtered(
    #         lambda att: att.check_in.date() in weekend_dates and att.days_work_include_late != 0
    #     )
    #
    #     return attendance_ids_filtered