import pytz

from datetime import datetime, timedelta

from odoo import models, fields, api, exceptions, _

from odoo.tools import format_datetime


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    is_bio_device = fields.Boolean(string='Created by Bio Device',store=True, default=False, readonly=True)
    created_by_user = fields.Integer(string='User Edit',store=True, group_operator='sum',readonly=True)
    edit_source = fields.Selection([
        ('user', 'User'),
        ('bio_device', 'Bio Device')
        ], string="Edit Source", compute='_compute_edit_source', store=True, readonly=True )
    alert_flag = fields.Integer(string='Alert',store=True, group_operator='sum',readonly=True)

    def write(self, vals):
        if 'is_bio_device' not in vals:
            # Only update is_bio_device if check_in or check_out is being modified
            if 'check_in' in vals or 'check_out' in vals or 'employee_id' in vals:
                for rec in self:
                    # Preserve True if it's already set
                    if rec.is_bio_device:
                        vals['is_bio_device'] = False
        return super().write(vals)

    @api.depends('create_uid', 'write_uid', 'is_bio_device')
    def _compute_edit_source(self):
        for record in self:
            if record.is_bio_device:
                record.edit_source = 'bio_device'
                record.created_by_user = '0'
            else:
                record.edit_source = 'user'
                record.created_by_user = '1'

    @api.depends('check_in', 'check_out', 'worked_hours')
    def _compute_color(self):
        for attendance in self:
            color = 0
            alert = 0

            if attendance.check_out:
                if attendance.worked_hours == 0:
                    color = 1
                    alert = 1
                elif attendance.worked_hours > 16:
                    color = 1
                    alert = 1
                elif attendance.check_out < attendance.check_in + timedelta(minutes=10):
                    color = 2
                    alert = 1
                else:
                    # Check for single check-in per day
                    same_day_check_ins = self.env['hr.attendance'].search_count([
                        ('employee_id', '=', attendance.employee_id.id),
                        ('check_in', '>=', attendance.check_in.replace(hour=0, minute=0, second=0, microsecond=0)),
                        ('check_in', '<',
                         (attendance.check_in + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0))
                    ])
                    if same_day_check_ins == 1:
                        color = 2
                        alert = 1
            else:
                # No check out — check if it’s an old entry
                if attendance.check_in and attendance.check_in < (datetime.today() - timedelta(days=1)):
                    color = 1
                    alert = 1
                else:
                    color = 10  # Optional: fallback color

            attendance.color = color
            attendance.alert_flag = alert

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        for attendance in self:
            # we take the latest attendance before our check_in time and check it doesn't overlap with ours
            last_attendance_before_check_in = self.env['hr.attendance'].search([
                ('employee_id', '=', attendance.employee_id.id),
                ('check_in', '<=', attendance.check_in),
                ('id', '!=', attendance.id),
            ], order='check_in desc', limit=1)
            if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
                raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s",
                                                   empl_name=attendance.employee_id.name,
                                                   datetime=format_datetime(self.env, attendance.check_in, dt_format=False)))

            if not attendance.check_out:
                # if our attendance is "open" (no check_out), create check-out
                # for last "open" check-in set time to 5 minute after "open" check-in
                no_check_out_attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_out', '=', False),
                    ('id', '!=', attendance.id),
                ], order='check_in desc')
                if no_check_out_attendances:
                    # If there's another "open" attendance, set its check_out time to check_in + 5 minutes
                    for no_check_out_attendance in no_check_out_attendances:
                        check_in_time = no_check_out_attendance.check_in
                        new_check_out_time = fields.Datetime.from_string(check_in_time) + timedelta(minutes=5)
                        # Update the record
                        no_check_out_attendance.write({
                            'check_out': fields.Datetime.to_string(new_check_out_time),
                            'is_bio_device': True
                        })

            # else:
            #     # we verify that the latest attendance with check_in time before our check_out time
            #     # is the same as the one before our check_in time computed before, otherwise it overlaps
            #     last_attendance_before_check_out = self.env['hr.attendance'].search([
            #         ('employee_id', '=', attendance.employee_id.id),
            #         ('check_in', '<', attendance.check_out),
            #         ('id', '!=', attendance.id),
            #     ], order='check_in desc', limit=1)
            #     if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
            #         raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s",
            #                                            empl_name=attendance.employee_id.name,
            #                                            datetime=format_datetime(self.env, last_attendance_before_check_out.check_in, dt_format=False)))

    # @api.constrains('check_in', 'check_out')
    # def _check_validity_check_in_check_out(self):
    #     """Verifies if check_in is earlier than check_out and provides detailed error info."""
    #     for attendance in self:
    #         if attendance.check_in and attendance.check_out:
    #             if attendance.check_out < attendance.check_in:
    #                 raise exceptions.ValidationError(_(
    #                     'Invalid time for %s:\n- Check In: %s\n- Check Out: %s\n\n"Check Out" time cannot be earlier than "Check In".'
    #                 ) % (
    #                                                      attendance.employee_id.name or 'Unknown Employee',
    #                                                      fields.Datetime.to_string(attendance.check_in),
    #                                                      fields.Datetime.to_string(attendance.check_out),
    #                                                  ))
    @api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        """ Disable the original constraint on check-in/check-out time order. """
        pass