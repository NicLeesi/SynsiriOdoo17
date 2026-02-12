# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import pytz
import logging
import datetime
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta
from pytz import timezone

_logger = logging.getLogger(__name__)
try:
    from zk import ZK, const
except ImportError:
    _logger.error("Please Install pyzk library.")


class BiometricDeviceDetails(models.Model):
    """Model for configuring and connect the biometric device with odoo"""
    _name = 'biometric.device.details'
    _description = 'Biometric Device Details'

    name = fields.Char(string='Name', required=True, help='Record Name')
    device_ip = fields.Char(string='Device IP', required=True,
                            help='The IP address of the Device')
    port_number = fields.Integer(string='Port Number', required=True,
                                 help="The Port Number of the Device")
    address_id = fields.Many2one('res.partner', string='Working Address',
                                 help='Working address of the partner')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda
                                     self: self.env.user.company_id.id,
                                 help='Current Company')

    def _get_next_call(self):
        next_call = (datetime.now() + timedelta(days=1)).replace(hour=22, minute=0, second=0)
        return next_call.strftime('%Y-%m-%d %H:%M:%S')

    def device_connect(self, zk):
        """Function for connecting the device with Odoo"""
        try:
            conn = zk.connect()
            return conn
        except Exception:
            return False

    def action_test_connection(self):
        """Checking the connection status"""
        zk = ZK(self.device_ip, port=self.port_number, timeout=30,
                password=False, ommit_ping=False)
        try:
            if zk.connect():
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': 'Successfully Connected',
                        'type': 'success',
                        'sticky': False
                    }
                }
        except Exception as error:
            raise ValidationError(f'{error}')

    def action_clear_attendance(self):
        """Methode to clear record from the zk.machine.attendance model and
        from the device"""
        for info in self:
            try:
                machine_ip = info.device_ip
                zk_port = info.port_number
                try:
                    # Connecting with the device
                    zk = ZK(machine_ip, port=zk_port, timeout=30,
                            password=0, force_udp=False, ommit_ping=False)
                except NameError:
                    raise UserError(_(
                        "Please install it with 'pip3 install pyzk'."))
                conn = self.device_connect(zk)
                if conn:
                    conn.enable_device()
                    clear_data = zk.get_attendance()
                    if clear_data:
                        # Clearing data in the device
                        conn.clear_attendance()
                        # Clearing data from attendance log
                        self._cr.execute(
                            """delete from zk_machine_attendance""")
                        conn.disconnect()
                    else:
                        raise UserError(
                            _('Unable to clear Attendance log.Are you sure '
                              'attendance log is not empty.'))
                else:
                    raise UserError(
                        _('Unable to connect to Attendance Device. Please use '
                          'Test Connection button to verify.'))
            except Exception as error:
                raise ValidationError(f'{error}')


    # 36 % FASTER VERSION
    def action_download_attendance(self):
        """(Schedule method) Function to download attendance records from the device"""
        _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")
        zk_attendance = self.env['zk.machine.attendance']
        hr_attendance = self.env['hr.attendance']

        for info in self:
            machine_ip = info.device_ip
            zk_port = info.port_number
            try:
                zk = ZK(machine_ip, port=zk_port, timeout=15, password=0,
                        force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(_("Pyzk module not Found. Please install it with 'pip3 install pyzk'."))

            conn = self.device_connect(zk)
            if conn:
                conn.disable_device()
                users = conn.get_users()
                attendance = conn.get_attendance()

                if attendance:
                    # ✅ OPTIMIZATION 1: Create user lookup dictionary
                    user_dict = {uid.user_id: uid for uid in users}

                    # ✅ OPTIMIZATION 2: Pre-process attendance data for batch operations
                    attendance_data = []
                    for each in attendance:
                        atten_time = each.timestamp
                        local_tz = pytz.timezone(self.env.user.partner_id.tz or 'GMT')
                        local_dt = local_tz.localize(atten_time, is_dst=None)
                        utc_dt = local_dt.astimezone(pytz.utc)
                        utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                        atten_time = datetime.datetime.strptime(utc_dt, "%Y-%m-%d %H:%M:%S")
                        atten_time_str = fields.Datetime.to_string(atten_time)

                        attendance_data.append({
                            'user_id': each.user_id,
                            'status': each.status,
                            'atten_time': atten_time_str,
                            'local_dt': local_dt
                        })

                    # ✅ OPTIMIZATION 3: Batch fetch all employees at once
                    device_ids = list(set(data['user_id'] for data in attendance_data))
                    employees = self.env['hr.employee'].with_context(active_test=False).search([
                        ('device_id_num', 'in', device_ids)
                    ])
                    employee_dict = {emp.device_id_num: emp for emp in employees}

                    # ✅ OPTIMIZATION 4: Batch check for duplicates
                    atten_times = [data['atten_time'] for data in attendance_data]
                    existing_punches = zk_attendance.search([
                        ('device_id_num', 'in', device_ids),
                        ('punching_time', 'in', atten_times)
                    ])
                    existing_set = {(p.device_id_num, p.punching_time) for p in existing_punches}

                    # Get config parameters ONCE (not inside loop!)
                    morning_start = float(self.env['ir.config_parameter'].sudo().get_param('morning_start'))
                    morning_end = float(self.env['ir.config_parameter'].sudo().get_param('morning_end'))
                    break_a_start = float(self.env['ir.config_parameter'].sudo().get_param('break_a_start'))
                    break_a_end = float(self.env['ir.config_parameter'].sudo().get_param('break_a_end'))
                    break_b_start = float(self.env['ir.config_parameter'].sudo().get_param('break_b_start'))
                    break_b_end = float(self.env['ir.config_parameter'].sudo().get_param('break_b_end'))
                    afternoon_start = float(self.env['ir.config_parameter'].sudo().get_param('afternoon_start'))
                    afternoon_end = float(self.env['ir.config_parameter'].sudo().get_param('afternoon_end'))

                    zk_attendance_vals = []

                    for data in attendance_data:
                        user_id = data['user_id']
                        atten_time = data['atten_time']
                        local_dt = data['local_dt']

                        # ✅ Direct lookup instead of nested loop
                        uid = user_dict.get(user_id)
                        if not uid:
                            continue

                        # ✅ Direct lookup instead of search
                        get_user_id = employee_dict.get(user_id)

                        if get_user_id:
                            # ✅ Set lookup instead of search - O(1)
                            if (user_id, atten_time) in existing_set:
                                continue  # Skip duplicate

                            # ✅ Convert hour + minutes to decimal (e.g., 9:30 AM = 9.5)
                            current_time = local_dt.hour + (local_dt.minute / 60.0)

                            # Determine punch type
                            punch_type = '1'
                            if morning_start <= current_time < morning_end:
                                punch_type = '0'
                            elif break_a_start <= current_time < break_a_end or \
                                    break_b_start <= current_time < break_b_end:

                                # ✅ FIRST: Check in-memory list (current batch)
                                last_punch_type = None
                                for zk_val in reversed(zk_attendance_vals):
                                    if zk_val['employee_id'] == get_user_id.id:
                                        last_punch_type = zk_val['punch_type']
                                        break

                                # ✅ SECOND: If not found in memory, search database
                                if last_punch_type is None:
                                    last_punch = zk_attendance.search(
                                        [('employee_id', '=', get_user_id.id)],
                                        order='punching_time desc', limit=1
                                    )
                                    if last_punch:
                                        last_punch_type = last_punch.punch_type

                                # ✅ Now check the last punch type
                                if last_punch_type == '1':
                                    punch_type = '0'

                            elif afternoon_start <= current_time < afternoon_end:
                                punch_type = '0'

                            # ✅ COLLECT zk_attendance data
                            zk_attendance_vals.append({
                                'employee_id': get_user_id.id,
                                'device_id_num': user_id,
                                'attendance_type': str(data['status']),
                                'punch_type': str(punch_type),
                                'punching_time': atten_time,
                                'address_id': info.address_id.id
                            })
                        else:
                            # Create new employee
                            employee = self.env['hr.employee'].create({
                                'device_id_num': user_id,
                                'name': uid.name
                            })

                            zk_attendance_vals.append({
                                'employee_id': employee.id,
                                'device_id_num': user_id,
                                'attendance_type': str(data['status']),
                                'punch_type': '0',
                                'punching_time': atten_time,
                                'address_id': info.address_id.id
                            })

                    # ✅ BATCH CREATE zk.machine.attendance records
                    if zk_attendance_vals:
                        zk_attendance.create(zk_attendance_vals)

                    # ✅ MEMORY MATCHING: Build lookup dictionaries
                    pending_punches_by_employee = {}

                    for zk_val in zk_attendance_vals:
                        emp_id = zk_val['employee_id']
                        if emp_id not in pending_punches_by_employee:
                            pending_punches_by_employee[emp_id] = []
                        pending_punches_by_employee[emp_id].append({
                            'time': zk_val['punching_time'],
                            'type': zk_val['punch_type']
                        })

                    # Sort punches by time for each employee
                    for emp_id in pending_punches_by_employee:
                        pending_punches_by_employee[emp_id].sort(key=lambda x: x['time'])

                    # ✅ PROCESS hr.attendance records with memory matching
                    hr_attendance_create_vals = []
                    hr_attendance_to_update = []

                    # ✅ OPTIMIZATION 5: Batch fetch all HR attendances
                    employee_ids = list(pending_punches_by_employee.keys())

                    # Fetch all open attendances in ONE query
                    open_attendances = hr_attendance.search([
                        ('employee_id', 'in', employee_ids),
                        ('check_out', '=', False)
                    ])
                    open_attendance_dict = {att.employee_id.id: att for att in open_attendances}

                    # Fetch all attendances for these employees in ONE query
                    all_attendances = hr_attendance.search([
                        ('employee_id', 'in', employee_ids)
                    ], order='employee_id, check_in desc')

                    # Group by employee, keeping only most recent
                    last_attendance_dict = {}
                    for att in all_attendances:
                        if att.employee_id.id not in last_attendance_dict:
                            last_attendance_dict[att.employee_id.id] = att

                    for emp_id, punches in pending_punches_by_employee.items():
                        # Get existing open attendance for this employee
                        open_attendance = open_attendance_dict.get(emp_id)

                        for punch in punches:
                            punch_time = punch['time']
                            punch_type = punch['type']

                            if punch_type == '0':  # Check-in
                                if not open_attendance:
                                    # No open attendance, check if this is a new day
                                    last_attendance = last_attendance_dict.get(emp_id)

                                    should_create = True
                                    if last_attendance:
                                        last_date = last_attendance.check_in.date()
                                        current_date = fields.Datetime.from_string(punch_time).date()
                                        if current_date <= last_date:
                                            should_create = False

                                    if should_create:
                                        # Create new check-in
                                        hr_attendance_create_vals.append({
                                            'employee_id': emp_id,
                                            'check_in': punch_time,
                                            'is_bio_device': True
                                        })
                                        # Mark as open (in memory)
                                        open_attendance = 'pending'
                                else:
                                    # Already has open attendance, check if new day
                                    if open_attendance != 'pending':
                                        last_date = open_attendance.check_in.date()
                                    else:
                                        # Get date from last created check-in
                                        last_created = [v for v in hr_attendance_create_vals if
                                                        v['employee_id'] == emp_id]
                                        if last_created:
                                            last_date = fields.Datetime.from_string(last_created[-1]['check_in']).date()
                                        else:
                                            last_date = None

                                    current_date = fields.Datetime.from_string(punch_time).date()

                                    if last_date and current_date > last_date:
                                        # New day, create new check-in
                                        hr_attendance_create_vals.append({
                                            'employee_id': emp_id,
                                            'check_in': punch_time,
                                            'is_bio_device': True
                                        })
                                        open_attendance = 'pending'

                            else:  # Check-out (punch_type == '1')
                                if open_attendance and open_attendance != 'pending':
                                    # Update existing open record
                                    hr_attendance_to_update.append((open_attendance, {
                                        'check_out': punch_time,
                                        'is_bio_device': True
                                    }))
                                    open_attendance = None
                                elif open_attendance == 'pending':
                                    # Find the last created check-in for this employee and add check-out
                                    for i in range(len(hr_attendance_create_vals) - 1, -1, -1):
                                        if hr_attendance_create_vals[i]['employee_id'] == emp_id and 'check_out' not in \
                                                hr_attendance_create_vals[i]:
                                            hr_attendance_create_vals[i]['check_out'] = punch_time
                                            open_attendance = None
                                            break
                                else:
                                    # No open attendance - check database
                                    last_attendance = last_attendance_dict.get(emp_id)

                                    if not last_attendance:
                                        # No record at all - create with estimated check-in
                                        estimated_check_in = fields.Datetime.from_string(punch_time) - timedelta(
                                            minutes=5)
                                        hr_attendance_create_vals.append({
                                            'employee_id': emp_id,
                                            'check_in': fields.Datetime.to_string(estimated_check_in),
                                            'check_out': punch_time,
                                            'is_bio_device': True
                                        })
                                    elif last_attendance.check_out:
                                        # Last record already closed
                                        estimated_check_in = fields.Datetime.from_string(punch_time) - timedelta(
                                            minutes=5)

                                        # Check if would overlap with the last record
                                        if last_attendance.check_out <= estimated_check_in:
                                            # Safe to create - no overlap
                                            hr_attendance_create_vals.append({
                                                'employee_id': emp_id,
                                                'check_in': fields.Datetime.to_string(estimated_check_in),
                                                'check_out': punch_time,
                                                'is_bio_device': True
                                            })
                                    else:
                                        # Last attendance exists and is OPEN - update it
                                        hr_attendance_to_update.append((last_attendance, {
                                            'check_out': punch_time,
                                            'is_bio_device': True
                                        }))

                    # ✅ BATCH CREATE hr.attendance records
                    if hr_attendance_create_vals:
                        hr_attendance.create(hr_attendance_create_vals)

                    # ✅ BATCH UPDATE hr.attendance records
                    if hr_attendance_to_update:
                        # Group records with same update values
                        update_groups = {}
                        for record, vals in hr_attendance_to_update:
                            vals_key = (vals.get('check_out'), vals.get('is_bio_device'))
                            if vals_key not in update_groups:
                                update_groups[vals_key] = (self.env['hr.attendance'], vals)
                            update_groups[vals_key] = (update_groups[vals_key][0] | record, vals)

                        # Execute batch writes
                        for records, vals in update_groups.values():
                            records.write(vals)

                    conn.disconnect()
                    return True
                else:
                    raise UserError(_('Unable to get the attendance log, please try again later.'))
            else:
                raise UserError(_('Unable to connect, please check the parameters and network connections.'))

    ##Original Version
    # def action_download_attendance(self):
    #     """ (Schedule method) Function to download attendance records from the device"""
    #     _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")
    #     zk_attendance = self.env['zk.machine.attendance']
    #     hr_attendance = self.env['hr.attendance']
    #     for info in self:
    #         machine_ip = info.device_ip
    #         zk_port = info.port_number
    #         try:
    #             # Connecting with the device with the ip and port provided
    #             zk = ZK(machine_ip, port=zk_port, timeout=15,
    #                     password=0,
    #                     force_udp=False, ommit_ping=False)
    #         except NameError:
    #             raise UserError(
    #                 _("Pyzk module not Found. Please install it"
    #                   "with 'pip3 install pyzk'."))
    #         conn = self.device_connect(zk)
    #         if conn:
    #             conn.disable_device()  # Device Cannot be used during this time.
    #             users = conn.get_users()
    #             attendance = conn.get_attendance()
    #             if attendance:
    #                 for each in attendance:
    #                     atten_time = each.timestamp
    #                     local_tz = pytz.timezone(
    #                         self.env.user.partner_id.tz or 'GMT')
    #                     local_dt = local_tz.localize(atten_time, is_dst=None)
    #                     utc_dt = local_dt.astimezone(pytz.utc)
    #                     utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
    #                     atten_time = datetime.datetime.strptime(
    #                         utc_dt, "%Y-%m-%d %H:%M:%S")
    #                     atten_time = fields.Datetime.to_string(atten_time)
    #
    #                     for uid in users:
    #                         if uid.user_id == each.user_id:
    #                             get_user_id = self.env['hr.employee'].with_context(active_test=False).search(
    #                                 [('device_id_num', '=', each.user_id)],
    #                                 limit=1
    #                             )
    #                             if get_user_id:
    #                                 duplicate_atten_ids = zk_attendance.search(
    #                                     [('device_id_num', '=', each.user_id),
    #                                      ('punching_time', '=', atten_time)])
    #                                 if not duplicate_atten_ids:
    #                                     morning_start = float(self.env['ir.config_parameter'].sudo().get_param(
    #                                         'morning_start'))
    #                                     morning_end = float(self.env['ir.config_parameter'].sudo().get_param(
    #                                         'morning_end'))
    #                                     break_a_start = float(self.env['ir.config_parameter'].sudo().get_param(
    #                                         'break_a_start'))
    #                                     break_a_end = float(self.env['ir.config_parameter'].sudo().get_param(
    #                                         'break_a_end'))
    #                                     break_b_start = float(self.env['ir.config_parameter'].sudo().get_param(
    #                                         'break_b_start'))
    #                                     break_b_end = float(self.env['ir.config_parameter'].sudo().get_param(
    #                                         'break_b_end'))
    #                                     afternoon_start = float(self.env['ir.config_parameter'].sudo().get_param(
    #                                         'afternoon_start'))
    #                                     afternoon_end = float(self.env['ir.config_parameter'].sudo().get_param(
    #                                         'afternoon_end'))
    #
    #                                     # ✅ Convert hour + minutes to decimal (e.g., 9:30 AM = 9.5)
    #                                     current_time = local_dt.hour + (local_dt.minute / 60.0)
    #
    #                                     # Determine punch type
    #                                     punch_type = '1'
    #                                     if morning_start <= current_time < morning_end:
    #                                         punch_type = '0'
    #                                     elif break_a_start <= current_time < break_a_end or \
    #                                             break_b_start <= current_time < break_b_end:
    #                                         last_punch = zk_attendance.search(
    #                                             [('employee_id', '=', get_user_id.id)],
    #                                             order='punching_time desc', limit=1
    #                                         )
    #                                         if last_punch and last_punch.punch_type == '1':
    #                                             punch_type = '0'
    #                                     elif afternoon_start <= current_time < afternoon_end:
    #                                         punch_type = '0'
    #
    #                                     zk_attendance.create({
    #                                         'employee_id': get_user_id.id,
    #                                         'device_id_num': each.user_id,
    #                                         'attendance_type': str(each.status),
    #                                         'punch_type': str(punch_type),
    #                                         'punching_time': atten_time,
    #                                         'address_id': info.address_id.id
    #                                     })
    #
    #                                     att_var = hr_attendance.search([(
    #                                         'employee_id', '=', get_user_id.id),
    #                                         ('check_out', '=', False)])
    #
    #                                     if punch_type == '0':
    #                                         if not att_var:
    #                                             hr_attendance.create({
    #                                                 'employee_id': get_user_id.id,
    #                                                 'check_in': atten_time,
    #                                                 'is_bio_device': True
    #                                             })
    #                                         if att_var:
    #                                             last_punch = hr_attendance.search(
    #                                                 [('employee_id', '=', get_user_id.id)],
    #                                                 order='check_in desc', limit=1)
    #
    #                                             last_punch_date = last_punch.check_in.date()
    #                                             atten_time_date = fields.Datetime.from_string(atten_time).date()
    #
    #                                             if atten_time_date > last_punch_date:
    #                                                 hr_attendance.create({
    #                                                     'employee_id': get_user_id.id,
    #                                                     'check_in': atten_time,
    #                                                     'is_bio_device': True
    #                                                 })
    #                                     else:  # check-out
    #                                         if len(att_var) == 1:
    #                                             att_var.write({
    #                                                 'check_out': atten_time,
    #                                                 'is_bio_device': True
    #                                             })
    #                                         else:
    #                                             att_var1 = hr_attendance.search(
    #                                                 [('employee_id', '=', get_user_id.id)])
    #                                             if att_var1:
    #                                                 att_var1[-1].write({
    #                                                     'check_out': atten_time,
    #                                                     'is_bio_device': True
    #                                                 })
    #                             else:
    #                                 employee = self.env['hr.employee'].create({
    #                                     'device_id_num': each.user_id,
    #                                     'name': uid.name
    #                                 })
    #                                 zk_attendance.create({
    #                                     'employee_id': employee.id,
    #                                     'device_id_num': each.user_id,
    #                                     'attendance_type': str(each.status),
    #                                     'punch_type': '0',
    #                                     'punching_time': atten_time,
    #                                     'address_id': info.address_id.id
    #                                 })
    #                                 hr_attendance.create({
    #                                     'employee_id': employee.id,
    #                                     'check_in': atten_time,
    #                                     'is_bio_device': True
    #                                 })
    #                 conn.disconnect()
    #                 return True
    #             else:
    #                 raise UserError(_('Unable to get the attendance log, please try again later.'))
    #         else:
    #             raise UserError(_('Unable to connect, please check the parameters and network connections.'))


    def action_restart_device(self):
        """For restarting the device"""
        zk = ZK(self.device_ip, port=self.port_number, timeout=15,
                password=0,
                force_udp=False, ommit_ping=False)
        self.device_connect(zk).restart()
