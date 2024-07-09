import pytz

from collections import defaultdict
from datetime import datetime, timedelta
from operator import itemgetter
from pytz import timezone

from odoo import models, fields, api, exceptions, _
from odoo.addons.resource.models.utils import Intervals
from odoo.tools import format_datetime
from odoo.osv.expression import AND, OR
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import AccessError
from odoo.tools import format_duration

class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def _compute_color(self):
        for attendance in self:
            if attendance.check_out:
                attendance.color = 1 if attendance.worked_hours > 16 else 0
                attendance.color = 1 if attendance.check_out < attendance.check_in + timedelta(minutes=10) else 0
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
            print("last:",last_attendance_before_check_in)
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
                            'check_out': fields.Datetime.to_string(new_check_out_time)
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

@api.constrains('check_in', 'check_out')
def _check_validity_check_in_check_out(self):
    """ Overwrite the method to not verifies if check_in is earlier than check_out. """
    pass
