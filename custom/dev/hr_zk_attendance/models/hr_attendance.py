import pytz

from datetime import datetime, timedelta

from odoo import models, fields, api, exceptions, _

from odoo.tools import format_datetime


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    is_bio_device = fields.Boolean(string='Created/Edited by Bio Device', default=False, readonly=True)
    edit_source = fields.Selection([
        ('user', 'User'),
        ('bio_device', 'Bio Device')
        ], string="Edit Source", compute='_compute_edit_source', store=True, readonly=True)

    def write(self, vals):
        if 'is_bio_device' not in vals:
            vals['is_bio_device'] = False
        return super(HrAttendance, self).write(vals)

    @api.depends('create_uid', 'write_uid', 'is_bio_device')
    def _compute_edit_source(self):
        for record in self:
            if record.is_bio_device:
                record.edit_source = 'bio_device'
            else:
                record.edit_source = 'user'

    def _compute_color(self):
        for attendance in self:
            if attendance.check_out:
                attendance.color = 1 if attendance.worked_hours > 16 else 0
                attendance.color = 2 if attendance.check_out < attendance.check_in + timedelta(minutes=10) else 0
                # Check for the number of check-ins on the same day
                same_day_check_ins = self.env['hr.attendance'].search_count([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_in', '>=', attendance.check_in.replace(hour=0, minute=0, second=0, microsecond=0)),
                    ('check_in', '<', (attendance.check_in + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0))
                ])
                # Set color to 2 if there is only one check-in for that day
                if same_day_check_ins == 1:
                    attendance.color = 2

            else:
                attendance.color = 1 if attendance.check_in < (datetime.today() - timedelta(days=1)) else 10

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