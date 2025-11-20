from odoo import models, fields, api
from datetime import datetime, timedelta, time
import pytz
import logging

_logger = logging.getLogger(__name__)


class HrAttendanceReportWizard(models.TransientModel):
    _name = 'hr.attendance.report.wizard'
    _description = 'Attendance Report Wizard'

    date_from = fields.Date(
        string='From Date',
        required=True,
        default=lambda self: fields.Date.today().replace(day=1)
    )
    date_to = fields.Date(
        string='To Date',
        required=True,
        default=fields.Date.today
    )
    employee_ids = fields.Many2many(
        'hr.employee',
        string='Employees',
        help='Leave empty for all employees'
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department'
    )

    def _is_work_day(self, employee, check_date):
        """Check if the given date is a work day for the employee"""
        if not employee.resource_calendar_id:
            return False

        # Use employee's timezone or calendar's timezone or UTC
        tz_name = employee.tz or employee.resource_calendar_id.tz or 'UTC'
        tz = pytz.timezone(tz_name)

        # Create timezone-aware datetime objects
        day_start = tz.localize(datetime.combine(check_date, time.min))
        day_end = tz.localize(datetime.combine(check_date, time.max))

        work_intervals = employee.resource_calendar_id._work_intervals_batch(
            day_start,
            day_end,
            resources=employee.resource_id,
        )

        employee_intervals = work_intervals.get(employee.resource_id.id, [])
        intervals_list = list(employee_intervals)

        return len(intervals_list) > 0

    def _calculate_absent_deduction(self, days_work_include_late, is_work_day):
        """
        Calculate absent deduction based on days_work_include_late and work day status

        Work day:
        - days_work = 1 → 0
        - days_work = 0.5 → -0.5
        - days_work = 0 → -1

        Off day:
        - days_work = 1 → 1
        - days_work = 0.5 → 0.5
        - days_work = 0 → 0
        """
        if is_work_day:
            if days_work_include_late >= 1:
                return 0
            elif days_work_include_late >= 0.5:
                return -0.5
            else:
                return -1
        else:
            # Off day - return positive value for extra work
            return days_work_include_late

    def action_generate_report(self):
        """Generate attendance summary records"""
        self.ensure_one()

        _logger.info("Starting attendance report generation...")

        # Get user timezone
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')

        # Clear old report data
        old_records = self.env['hr.attendance.report.line'].search([])
        _logger.info("Deleting %s old records", len(old_records))
        old_records.unlink()

        # Get employees
        if self.employee_ids:
            employees = self.employee_ids
        elif self.department_id:
            employees = self.env['hr.employee'].search([
                ('department_id', 'child_of', self.department_id.id),
                ('active', '=', True)
            ])
        else:
            employees = self.env['hr.employee'].search([('active', '=', True)])

        _logger.info("Processing %s employees", len(employees))

        if not employees:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning',
                    'message': 'No employees found for the selected criteria.',
                    'type': 'warning',
                }
            }

        date_from = self.date_from
        date_to = self.date_to

        report_lines = []

        # Track absences per employee for penalty calculation
        employee_absences = {}

        for employee in employees:
            current_date = date_from
            employee_absences[employee.id] = 0  # Reset absence counter for each employee

            while current_date <= date_to:
                # Convert local date to UTC datetime range
                local_start = user_tz.localize(datetime.combine(current_date, datetime.min.time()))
                local_end = user_tz.localize(datetime.combine(current_date, datetime.max.time()))
                utc_start = local_start.astimezone(pytz.UTC).replace(tzinfo=None)
                utc_end = local_end.astimezone(pytz.UTC).replace(tzinfo=None)

                # Get ALL attendances for this day
                attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', utc_start),
                    ('check_in', '<=', utc_end),
                ])

                # Check leave
                leave = self.env['hr.leave'].search([
                    ('employee_id', '=', employee.id),
                    ('state', '=', 'validate'),
                    ('date_from', '<=', current_date),
                    ('date_to', '>=', current_date),
                ], limit=1)

                # Check if work day
                is_work_day = self._is_work_day(employee, current_date)

                # Determine status and values
                if attendances:
                    status = 'present'
                    worked_hours = sum(attendances.mapped('worked_hours')) or 0.0
                    days_work_include_late = sum(attendances.mapped('days_work_include_late')) or 0.0

                    late_check_in = 0
                    late_check_in_pm = 0

                    if 'late_check_in' in self.env['hr.attendance']._fields:
                        late_check_in = sum(attendances.mapped('late_check_in')) or 0


                    if 'late_check_in_afternoon' in self.env['hr.attendance']._fields:
                        late_check_in_pm = sum(attendances.mapped('late_check_in_afternoon')) or 0


                    is_present = 1
                    is_absent = 0
                    is_leave = 0

                elif leave:
                    status = 'leave'
                    worked_hours = 0.0
                    days_work_include_late = 1.0  # Leave counts as full day
                    late_check_in = 0
                    late_check_in_pm = 0
                    is_present = 0
                    is_absent = 0
                    is_leave = 1

                elif not is_work_day:
                    status = 'weekend'
                    worked_hours = 0.0
                    days_work_include_late = 0.0
                    late_check_in = 0
                    late_check_in_pm = 0
                    is_present = 0
                    is_absent = 0
                    is_leave = 0

                else:
                    status = 'absent'
                    worked_hours = 0.0
                    days_work_include_late = 0.0
                    late_check_in = 0
                    late_check_in_pm = 0
                    is_present = 0
                    is_absent = 1
                    is_leave = 0

                # Calculate absent deduction
                absent_deduction = self._calculate_absent_deduction(days_work_include_late, is_work_day)

                # Apply penalty for multiple absences
                if absent_deduction < 0:
                    # This is an absence
                    employee_absences[employee.id] += 1

                    # Apply penalty: 2nd absence onwards gets additional -1 penalty
                    if employee_absences[employee.id] > 1:
                        penalty = employee_absences[employee.id] - 1  # 2nd absence = 1 extra, 3rd = 2 extra, etc.
                        absent_deduction -= penalty
                        _logger.info(
                            "Employee: %s | Date: %s | Absence #%s | Base: -1 | Penalty: -%s | Total: %s",
                            employee.name, current_date, employee_absences[employee.id], penalty, absent_deduction
                        )

                # Create report line
                report_lines.append({
                    'employee_id': employee.id,
                    'department_id': employee.department_id.id if employee.department_id else False,
                    'date': current_date,
                    'worked_hours': worked_hours,
                    'days_work_include_late': days_work_include_late,
                    'late_check_in': late_check_in,
                    'late_check_in_afternoon': late_check_in_pm,
                    'leave_hours': 8.0 if leave else 0.0,
                    'status': status,
                    'is_work_day': is_work_day,
                    'absent_deduction': absent_deduction,
                    'is_absent': is_absent,
                    'is_weekend': 1 if not is_work_day and not attendances else 0,
                    'is_present': is_present,
                    'is_leave': is_leave,
                })

                current_date += timedelta(days=1)

        _logger.info("Creating %s report lines", len(report_lines))

        if report_lines:
            created_records = self.env['hr.attendance.report.line'].create(report_lines)
            _logger.info("Created %s records successfully", len(created_records))
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning',
                    'message': 'No data to generate.',
                    'type': 'warning',
                }
            }

        _logger.info("Returning action to view report")

        return {
            'name': 'Attendance Report',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.attendance.report.line',
            'view_mode': 'tree,pivot',
            'target': 'main',
        }

class HrAttendanceReportLine(models.TransientModel):
    _name = 'hr.attendance.report.line'
    _description = 'Attendance Report Line'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('hr.department', string='Department')
    date = fields.Date(string='Date')
    worked_hours = fields.Float(string='Worked Hours')
    days_work_include_late = fields.Float(string='Days Work')

    late_check_in = fields.Integer(string='Late AM (Min)')
    late_check_in_afternoon = fields.Integer(string='Late PM (Min)')

    leave_hours = fields.Float(string='Leave Hours')
    status = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('leave', 'Leave'),
        ('weekend', 'Weekend'),
    ], string='Status')

    # New fields
    is_work_day = fields.Boolean(string='Is Work Day')
    absent_deduction = fields.Float(string='Absent Deduction', digits=(10, 1) ) # The calculated absent value

    is_absent = fields.Integer(string='Absent')
    is_weekend = fields.Integer(string='Weekend')
    is_present = fields.Integer(string='Present')
    is_leave = fields.Integer(string='Leave')