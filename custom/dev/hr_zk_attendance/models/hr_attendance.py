from datetime import timedelta, datetime

from odoo import models, fields, api, exceptions, _
from odoo.tools import format_datetime
import pytz
import logging

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    is_bio_device = fields.Boolean(string='Created by Bio Device', store=True, default=False, readonly=True, index=True)
    created_by_user = fields.Integer(string='User Edit', store=True, group_operator='sum', readonly=True)
    edit_source = fields.Selection([
        ('user', 'User'),
        ('bio_device', 'Bio Device')
    ], string="Edit Source", compute='_compute_edit_source', store=True, readonly=True)
    alert_flag = fields.Integer(string='Alert', store=True, readonly=True)
    color = fields.Integer(string='Color', store=True, readonly=True)

    @api.depends('create_uid', 'write_uid', 'is_bio_device')
    def _compute_edit_source(self):
        for record in self:
            if record.is_bio_device:
                record.edit_source = 'bio_device'
                record.created_by_user = 0
            else:
                record.edit_source = 'user'
                record.created_by_user = 1

    @api.model
    def cron_compute_attendance_colors(self):
        """Scheduled action to compute colors for attendance records from last 60 days"""
        _logger.info("Starting daily attendance color computation (last 60 days)...")

        # ✅ Calculate date 60 days ago
        sixty_days_ago = datetime.now() - timedelta(days=60)
        sixty_days_ago = sixty_days_ago.replace(hour=0, minute=0, second=0, microsecond=0)

        # ✅ Get only attendance records from last 60 days
        recent_attendances = self.search([
            ('check_in', '>=', fields.Datetime.to_string(sixty_days_ago))
        ], order='check_in desc')

        total = len(recent_attendances)
        _logger.info(f"Computing colors for {total} attendance records (from {sixty_days_ago.date()})...")

        if total == 0:
            _logger.info("No attendance records found in the last 60 days")
            return True

        # ✅ Process in batches to avoid memory issues
        batch_size = 500
        for i in range(0, total, batch_size):
            batch = recent_attendances[i:i + batch_size]
            self._compute_colors_batch(batch)
            _logger.info(f"Processed {min(i + batch_size, total)}/{total} records")

        _logger.info("Daily attendance color computation completed!")
        return True

    def _compute_colors_batch(self, attendances):
        """Compute colors for a batch of attendance records"""
        # Cache to avoid duplicate queries for same employee/day
        cache = {}

        for attendance in attendances:
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
                    # Simple cache key
                    cache_key = (attendance.employee_id.id, attendance.check_in.date())

                    if cache_key not in cache:
                        cache[cache_key] = self.search_count([
                            ('employee_id', '=', attendance.employee_id.id),
                            ('check_in', '>=', attendance.check_in.replace(hour=0, minute=0, second=0, microsecond=0)),
                            ('check_in', '<',
                             (attendance.check_in + timedelta(days=1)).replace(hour=0, minute=0, second=0,
                                                                               microsecond=0))
                        ])

                    if cache[cache_key] == 1:
                        color = 2
                        alert = 1
            else:
                color = 10

            # ✅ Update without triggering other computations
            attendance.write({'color': color, 'alert_flag': alert})

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
                raise exceptions.ValidationError(_(
                    "Cannot create new attendance record for employee: %(empl_name)s.\n"
                    "New check-in: %(new_checkin)s\n"
                    "Conflicts with existing record:\n"
                    "  - Check-in: %(old_checkin)s\n"
                    "  - Check-out: %(old_checkout)s\n"
                    "Please correct the existing record first.",
                    empl_name=attendance.employee_id.name,
                    new_checkin=format_datetime(self.env, attendance.check_in, dt_format=False),
                    old_checkin=format_datetime(self.env, last_attendance_before_check_in.check_in, dt_format=False),
                    old_checkout=format_datetime(self.env, last_attendance_before_check_in.check_out, dt_format=False)
                ))

            if not attendance.check_out:
                # Only close forgotten check-ins from PREVIOUS calendar days
                no_check_out_attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_out', '=', False),
                    ('id', '!=', attendance.id),
                    ('check_in', '<', attendance.check_in),
                ], order='check_in desc')

                if no_check_out_attendances:
                    user_tz = pytz.timezone(self.env.user.tz or 'UTC')

                    current_check_in_utc = attendance.check_in
                    if current_check_in_utc.tzinfo is None:
                        current_check_in_utc = pytz.utc.localize(current_check_in_utc)
                    else:
                        current_check_in_utc = current_check_in_utc.astimezone(pytz.utc)
                    current_check_in_local = current_check_in_utc.astimezone(user_tz)
                    current_date = current_check_in_local.date()

                    for no_check_out_attendance in no_check_out_attendances:
                        old_check_in_utc = no_check_out_attendance.check_in
                        if old_check_in_utc.tzinfo is None:
                            old_check_in_utc = pytz.utc.localize(old_check_in_utc)
                        else:
                            old_check_in_utc = old_check_in_utc.astimezone(pytz.utc)
                        old_check_in_local = old_check_in_utc.astimezone(user_tz)
                        old_date = old_check_in_local.date()

                        if old_date < current_date:
                            check_in_time = no_check_out_attendance.check_in
                            new_check_out_time = check_in_time + timedelta(minutes=5)

                            no_check_out_attendance.write({
                                'check_out': fields.Datetime.to_string(new_check_out_time),
                                'is_bio_device': True
                            })

    @api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        """ Disable the original constraint on check-in/check-out time order. """
        pass






# from datetime import timedelta
#
# from odoo import models, fields, api, exceptions, _
#
# from odoo.tools import format_datetime
# import pytz
#
# class HrAttendance(models.Model):
#     _inherit = "hr.attendance"
#
#     is_bio_device = fields.Boolean(string='Created by Bio Device',store=True, default=False, readonly=True)
#     created_by_user = fields.Integer(string='User Edit',store=True, group_operator='sum',readonly=True)
#     edit_source = fields.Selection([
#         ('user', 'User'),
#         ('bio_device', 'Bio Device')
#         ], string="Edit Source", compute='_compute_edit_source', store=True, readonly=True )
#     alert_flag = fields.Integer(string='Alert', compute='_compute_color', group_operator='sum',readonly=True, store=True)
#     color = fields.Integer(
#         string='Color',
#         compute='_compute_color',
#         store=True,
#         readonly=True
#     )
#
#     @api.model_create_multi
#     def create(self, vals_list):
#         records = super().create(vals_list)
#         self._recompute_same_day_colors(records)
#         return records
#
#     def unlink(self):
#         affected_attendances = self.env['hr.attendance']
#
#         # ✅ Store IDs of records being deleted
#         deleted_ids = self.ids
#
#         for record in self:
#             if record.check_in:
#                 same_day = self.search([
#                     ('employee_id', '=', record.employee_id.id),
#                     ('check_in', '>=', record.check_in.replace(hour=0, minute=0, second=0, microsecond=0)),
#                     ('check_in', '<',
#                      (record.check_in + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)),
#                     ('id', '!=', record.id),
#                     ('id', 'not in', deleted_ids)  # ✅ EXCLUDE records being deleted
#                 ])
#                 affected_attendances |= same_day
#
#         result = super().unlink()
#
#         # ✅ Double-check: filter out any deleted records
#         if affected_attendances:
#             affected_attendances = affected_attendances.exists()  # Remove deleted records
#             if affected_attendances:
#                 affected_attendances._compute_color()
#
#         return result
#
#     def write(self, vals):
#         if 'is_bio_device' not in vals:
#             if 'check_in' in vals or 'check_out' in vals or 'employee_id' in vals:
#                 for rec in self:
#                     if rec.is_bio_device:
#                         vals['is_bio_device'] = False
#
#         result = super().write(vals)
#
#         # Only recompute if check_in or employee_id changed (affects same-day count)
#         if 'check_in' in vals or 'employee_id' in vals:
#             self._recompute_same_day_colors(self)
#
#         return result
#
#     @api.depends('create_uid', 'write_uid', 'is_bio_device')
#     def _compute_edit_source(self):
#         for record in self:
#             if record.is_bio_device:
#                 record.edit_source = 'bio_device'
#                 record.created_by_user = '0'
#             else:
#                 record.edit_source = 'user'
#                 record.created_by_user = '1'
#
#     def _recompute_same_day_colors(self, records):
#         """Optimized for bulk bio device operations"""
#         affected_attendances = self.env['hr.attendance']
#         seen_employee_days = set()
#
#         for record in records:
#             if record.check_in:
#                 day_start = record.check_in.replace(hour=0, minute=0, second=0, microsecond=0)
#                 emp_day_key = (record.employee_id.id, day_start)
#
#                 if emp_day_key not in seen_employee_days:
#                     seen_employee_days.add(emp_day_key)
#                     same_day = self.search([
#                         ('employee_id', '=', record.employee_id.id),
#                         ('check_in', '>=', day_start),
#                         ('check_in', '<', day_start + timedelta(days=1))
#                     ])
#                     affected_attendances |= same_day
#
#         if affected_attendances:
#             affected_attendances._compute_color()
#
#     @api.depends('check_in', 'check_out', 'worked_hours')
#     def _compute_color(self):
#         # Cache to avoid duplicate queries for same employee/day
#         cache = {}
#
#         for attendance in self:
#             color = 0
#             alert = 0
#
#             if attendance.check_out:
#                 if attendance.worked_hours == 0:
#                     color = 1
#                     alert = 1
#                 elif attendance.worked_hours > 16:
#                     color = 1
#                     alert = 1
#                 elif attendance.check_out < attendance.check_in + timedelta(minutes=10):
#                     color = 2
#                     alert = 1
#                 else:
#                     # Simple cache key
#                     cache_key = (attendance.employee_id.id, attendance.check_in.date())
#
#                     if cache_key not in cache:
#                         cache[cache_key] = self.env['hr.attendance'].search_count([
#                             ('employee_id', '=', attendance.employee_id.id),
#                             ('check_in', '>=', attendance.check_in.replace(hour=0, minute=0, second=0, microsecond=0)),
#                             ('check_in', '<',
#                              (attendance.check_in + timedelta(days=1)).replace(hour=0, minute=0, second=0,
#                                                                                microsecond=0))
#                         ])
#
#                     if cache[cache_key] == 1:
#                         color = 2
#                         alert = 1
#             else:
#                 color = 10
#
#             attendance.color = color
#             attendance.alert_flag = alert
#
#     @api.constrains('check_in', 'check_out', 'employee_id')
#     def _check_validity(self):
#         """ Verifies the validity of the attendance record compared to the others from the same employee.
#             For the same employee we must have :
#                 * maximum 1 "open" attendance record (without check_out)
#                 * no overlapping time slices with previous employee records
#         """
#         for attendance in self:
#             # we take the latest attendance before our check_in time and check it doesn't overlap with ours
#             last_attendance_before_check_in = self.env['hr.attendance'].search([
#                 ('employee_id', '=', attendance.employee_id.id),
#                 ('check_in', '<=', attendance.check_in),
#                 ('id', '!=', attendance.id),
#             ], order='check_in desc', limit=1)
#
#             if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
#                 # ✅ IMPROVED ERROR MESSAGE:
#                 raise exceptions.ValidationError(_(
#                     "Cannot create new attendance record for employee :  %(empl_name)s.\n"
#                     "New check-in: %(new_checkin)s\n"
#                     "Conflicts with existing record:\n"
#                     "  - Check-in: %(old_checkin)s\n"
#                     "  - Check-out: %(old_checkout)s\n"
#                     "Please correct the existing record first.",
#                     empl_name=attendance.employee_id.name,
#                     new_checkin=format_datetime(self.env, attendance.check_in, dt_format=False),
#                     old_checkin=format_datetime(self.env, last_attendance_before_check_in.check_in, dt_format=False),
#                     old_checkout=format_datetime(self.env, last_attendance_before_check_in.check_out, dt_format=False)
#                 ))
#
#             if not attendance.check_out:
#                 # ✅ Only close forgotten check-ins from PREVIOUS calendar days
#                 no_check_out_attendances = self.env['hr.attendance'].search([
#                     ('employee_id', '=', attendance.employee_id.id),
#                     ('check_out', '=', False),
#                     ('id', '!=', attendance.id),
#                     ('check_in', '<', attendance.check_in),  # ✅ Only BEFORE current check-in
#                 ], order='check_in desc')
#
#                 if no_check_out_attendances:
#                     # ✅ Get user timezone
#                     user_tz = pytz.timezone(self.env.user.tz or 'UTC')
#
#                     # ✅ Convert current record to local date
#                     current_check_in_utc = attendance.check_in
#                     if current_check_in_utc.tzinfo is None:
#                         current_check_in_utc = pytz.utc.localize(current_check_in_utc)
#                     else:
#                         current_check_in_utc = current_check_in_utc.astimezone(pytz.utc)
#                     current_check_in_local = current_check_in_utc.astimezone(user_tz)
#                     current_date = current_check_in_local.date()
#
#                     for no_check_out_attendance in no_check_out_attendances:
#                         # ✅ Convert old record to local date
#                         old_check_in_utc = no_check_out_attendance.check_in
#                         if old_check_in_utc.tzinfo is None:
#                             old_check_in_utc = pytz.utc.localize(old_check_in_utc)
#                         else:
#                             old_check_in_utc = old_check_in_utc.astimezone(pytz.utc)
#                         old_check_in_local = old_check_in_utc.astimezone(user_tz)
#                         old_date = old_check_in_local.date()
#
#                         # ✅ Only close if from PREVIOUS calendar day
#                         if old_date < current_date:
#                             check_in_time = no_check_out_attendance.check_in
#                             new_check_out_time = check_in_time + timedelta(minutes=5)
#
#                             no_check_out_attendance.write({
#                                 'check_out': fields.Datetime.to_string(new_check_out_time),
#                                 'is_bio_device': True
#                             })
#
#     @api.constrains('check_in', 'check_out')
#     def _check_validity_check_in_check_out(self):
#         """ Disable the original constraint on check-in/check-out time order. """
#         pass