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
from odoo import fields, models, _, api
from datetime import datetime, time
import pytz
import logging

_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    """Inherit the model to add fields and methods"""
    _inherit = 'hr.employee'

    late_check_in_count = fields.Integer(
        string="Late Check-In", compute="_compute_late_check_in_count",
        help="Count of employee's late checkin")

    is_day_off_today = fields.Boolean(
        string="Day Off Today",
        compute='_compute_is_day_off_today',
        search='_search_is_day_off_today',
        store=False
    )

    def action_to_open_late_check_in_records(self):
        """
            :return: dictionary defining the action to open the late check-in
            records window.
            :rtype: dict
        """
        return {
            'name': _('Employee Late Check-in'),
            'domain': [('employee_id', '=', self.id)],
            'res_model': 'late.check.in',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'limit': 80}

    def _compute_late_check_in_count(self):
        """Compute the late check-in count"""
        for rec in self:
            rec.late_check_in_count = self.env['late.check.in'].search_count(
                [('employee_id', '=', rec.id)])

    def _compute_is_day_off_today(self):
        """Check if today is a day off (weekend, holiday, or approved leave)"""
        today = fields.Date.today()

        for employee in self:
            if not employee.resource_calendar_id:
                employee.is_day_off_today = True
                continue

            # Use employee's timezone or calendar's timezone or UTC
            tz_name = employee.tz or employee.resource_calendar_id.tz or 'UTC'
            tz = pytz.timezone(tz_name)

            # Create timezone-aware datetime objects
            today_start = tz.localize(datetime.combine(today, time.min))
            today_end = tz.localize(datetime.combine(today, time.max))

            work_intervals = employee.resource_calendar_id._work_intervals_batch(
                today_start,
                today_end,
                resources=employee.resource_id,
            )

            employee_intervals = work_intervals.get(employee.resource_id.id, [])

            # Convert to list to check length
            intervals_list = list(employee_intervals)

            # Debug logging
            _logger.info(
                "Employee: %s | Calendar: %s | Date: %s | Intervals: %s | Count: %s",
                employee.name,
                employee.resource_calendar_id.name,
                today,
                intervals_list,
                len(intervals_list)
            )
            _logger.info(
                "Employee: %s | Calendar: %s | TZ: %s | Date: %s",
                employee.name,
                employee.resource_calendar_id.name,
                tz_name,
                today
            )

            employee.is_day_off_today = len(intervals_list) == 0

    @api.model
    def _search_is_day_off_today(self, operator, value):
        """Search for employees with day off today"""
        today = fields.Date.today()

        employees = self.search([])
        day_off_employees = []

        for employee in employees:
            if not employee.resource_calendar_id:
                day_off_employees.append(employee.id)
                continue

            # Use employee's timezone
            tz_name = employee.tz or employee.resource_calendar_id.tz or 'UTC'
            emp_tz = pytz.timezone(tz_name)
            emp_today_start = emp_tz.localize(datetime.combine(today, time.min))
            emp_today_end = emp_tz.localize(datetime.combine(today, time.max))

            work_intervals = employee.resource_calendar_id._work_intervals_batch(
                emp_today_start,
                emp_today_end,
                resources=employee.resource_id,
            )

            employee_intervals = work_intervals.get(employee.resource_id.id, [])
            intervals_list = list(employee_intervals)

            _logger.info(
                "Search - Employee: %s | Intervals count: %s",
                employee.name,
                len(intervals_list)
            )
            _logger.info(
                "Employee: %s | Calendar: %s | TZ: %s | Date: %s",
                employee.name,
                employee.resource_calendar_id.name,
                tz_name,
                today
            )

            if len(intervals_list) == 0:
                day_off_employees.append(employee.id)

        _logger.info("Day off employees: %s", day_off_employees)

        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('id', 'in', day_off_employees)]
        else:
            return [('id', 'not in', day_off_employees)]
