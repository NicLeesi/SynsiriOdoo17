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


    def action_download_attendance(self):
        """ (Schedule method) Function to download attendance records from the device"""
        _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")
        zk_attendance = self.env['zk.machine.attendance']
        hr_attendance = self.env['hr.attendance']
        for info in self:
            machine_ip = info.device_ip
            zk_port = info.port_number
            try:
                # Connecting with the device with the ip and port provided
                zk = ZK(machine_ip, port=zk_port, timeout=15,
                        password=0,
                        force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(
                    _("Pyzk module not Found. Please install it"
                      "with 'pip3 install pyzk'."))
            conn = self.device_connect(zk)
            if conn:
                conn.disable_device()  # Device Cannot be used during this time.
                users = conn.get_users()
                attendance = conn.get_attendance()
                if attendance:
                    for each in attendance:
                        atten_time = each.timestamp
                        local_tz = pytz.timezone(
                            self.env.user.partner_id.tz or 'GMT')
                        local_dt = local_tz.localize(atten_time, is_dst=None)
                        utc_dt = local_dt.astimezone(pytz.utc)
                        utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                        atten_time = datetime.datetime.strptime(
                            utc_dt, "%Y-%m-%d %H:%M:%S")
                        atten_time = fields.Datetime.to_string(atten_time)

                        for uid in users:
                            if uid.user_id == each.user_id:
                                get_user_id = self.env['hr.employee'].search(
                                    [('device_id_num', '=', each.user_id)])
                                if get_user_id:
                                    duplicate_atten_ids = zk_attendance.search(
                                        [('device_id_num', '=', each.user_id),
                                         ('punching_time', '=', atten_time)])
                                    if not duplicate_atten_ids:
                                        morning_start = float(self.env['ir.config_parameter'].sudo().get_param(
                                            'morning_start'))
                                        morning_end = float(self.env['ir.config_parameter'].sudo().get_param(
                                            'morning_end'))
                                        break_a_start = float(self.env['ir.config_parameter'].sudo().get_param(
                                            'break_a_start'))
                                        break_a_end = float(self.env['ir.config_parameter'].sudo().get_param(
                                            'break_a_end'))
                                        break_b_start = float(self.env['ir.config_parameter'].sudo().get_param(
                                            'break_b_start'))
                                        break_b_end = float(self.env['ir.config_parameter'].sudo().get_param(
                                            'break_b_end'))
                                        afternoon_start = float(self.env['ir.config_parameter'].sudo().get_param(
                                            'afternoon_start'))
                                        afternoon_end = float(self.env['ir.config_parameter'].sudo().get_param(
                                            'afternoon_end'))
                                        # Determine punch type based on time of day
                                        punch_type = '1'
                                        if morning_start <= float(local_dt.hour) < morning_end:

                                            punch_type = '0'
                                        elif break_a_start <= float(local_dt.hour) < break_a_end or break_b_start <= float(local_dt.hour) < break_b_end:
                                            last_punch = zk_attendance.search(
                                                [('employee_id', '=', get_user_id.id)],
                                                order='punching_time desc', limit=1)
                                            if last_punch and last_punch.punch_type == '1':
                                                punch_type = '0'
                                        elif afternoon_start <= float(local_dt.hour) < afternoon_end:
                                            punch_type = '0'

                                        zk_attendance.create({
                                            'employee_id': get_user_id.id,
                                            'device_id_num': each.user_id,
                                            'attendance_type': str(each.status),
                                            'punch_type': str(punch_type),
                                            'punching_time': atten_time,
                                            'address_id': info.address_id.id
                                        })

                                        att_var = hr_attendance.search([(
                                            'employee_id', '=', get_user_id.id),
                                            ('check_out', '=', False)])

                                        if punch_type == '0':
                                            if not att_var:
                                                hr_attendance.create({
                                                    'employee_id': get_user_id.id,
                                                    'check_in': atten_time,
                                                    'is_bio_device': True
                                                })
                                            if att_var:
                                                last_punch = hr_attendance.search(
                                                    [('employee_id', '=', get_user_id.id)],
                                                    order='check_in desc', limit=1)

                                                last_punch_date = last_punch.check_in.date()
                                                atten_time_date = fields.Datetime.from_string(atten_time).date()

                                                if atten_time_date > last_punch_date:

                                                    hr_attendance.create({
                                                        'employee_id': get_user_id.id,
                                                        'check_in': atten_time,
                                                        'is_bio_device': True
                                                    })
                                        else:  # check-out
                                            if len(att_var) == 1:
                                                att_var.write({
                                                    'check_out': atten_time
                                                })
                                            else:
                                                att_var1 = hr_attendance.search(
                                                    [('employee_id', '=', get_user_id.id)])
                                                if att_var1:
                                                    att_var1[-1].write({
                                                        'check_out': atten_time
                                                    })
                                else:
                                    employee = self.env['hr.employee'].create({
                                        'device_id_num': each.user_id,
                                        'name': uid.name
                                    })
                                    zk_attendance.create({
                                        'employee_id': employee.id,
                                        'device_id_num': each.user_id,
                                        'attendance_type': str(each.status),
                                        'punch_type': '0',
                                        'punching_time': atten_time,
                                        'address_id': info.address_id.id
                                    })
                                    hr_attendance.create({
                                        'employee_id': employee.id,
                                        'check_in': atten_time,
                                        'is_bio_device': True
                                    })
                    conn.disconnect()
                    # Call auto_update_attendance method
                    # self.auto_update_attendance()
                    return True
                else:
                    raise UserError(_('Unable to get the attendance log, please try again later.'))
            else:
                raise UserError(_('Unable to connect, please check the parameters and network connections.'))

    def action_download_attendance(self):
        """ (Schedule method) Function to download attendance records from the device"""
        _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")
        zk_attendance = self.env['zk.machine.attendance']
        hr_attendance = self.env['hr.attendance']
        for info in self:
            machine_ip = info.device_ip
            zk_port = info.port_number
            try:
                # Connecting with the device with the ip and port provided
                zk = ZK(machine_ip, port=zk_port, timeout=15,
                        password=0,
                        force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(
                    _("Pyzk module not Found. Please install it"
                      "with 'pip3 install pyzk'."))
            conn = self.device_connect(zk)
            if conn:
                conn.disable_device()  # Device Cannot be used during this time.
                users = conn.get_users()
                attendance = conn.get_attendance()
                if attendance:
                    for each in attendance:
                        atten_time = each.timestamp
                        local_tz = pytz.timezone(
                            self.env.user.partner_id.tz or 'GMT')
                        local_dt = local_tz.localize(atten_time, is_dst=None)
                        utc_dt = local_dt.astimezone(pytz.utc)
                        utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                        atten_time = datetime.datetime.strptime(
                            utc_dt, "%Y-%m-%d %H:%M:%S")
                        atten_time = fields.Datetime.to_string(atten_time)

                        for uid in users:
                            if uid.user_id == each.user_id:
                                get_user_id = self.env['hr.employee'].search(
                                    [('device_id_num', '=', each.user_id)])
                                if get_user_id:
                                    duplicate_atten_ids = zk_attendance.search(
                                        [('device_id_num', '=', each.user_id),
                                         ('punching_time', '=', atten_time)])
                                    if not duplicate_atten_ids:
                                        morning_start = float(self.env['ir.config_parameter'].sudo().get_param(
                                            'morning_start'))
                                        morning_end = float(self.env['ir.config_parameter'].sudo().get_param(
                                            'morning_end'))
                                        break_a_start = float(self.env['ir.config_parameter'].sudo().get_param(
                                            'break_a_start'))
                                        break_a_end = float(self.env['ir.config_parameter'].sudo().get_param(
                                            'break_a_end'))
                                        break_b_start = float(self.env['ir.config_parameter'].sudo().get_param(
                                            'break_b_start'))
                                        break_b_end = float(self.env['ir.config_parameter'].sudo().get_param(
                                            'break_b_end'))
                                        afternoon_start = float(self.env['ir.config_parameter'].sudo().get_param(
                                            'afternoon_start'))
                                        afternoon_end = float(self.env['ir.config_parameter'].sudo().get_param(
                                            'afternoon_end'))
                                        # Determine punch type based on time of day
                                        punch_type = '1'
                                        if morning_start <= float(local_dt.hour) < morning_end:
                                            punch_type = '0'
                                        elif break_a_start <= float(
                                                local_dt.hour) < break_a_end or break_b_start <= float(
                                            local_dt.hour) < break_b_end:
                                            last_punch = zk_attendance.search(
                                                [('employee_id', '=', get_user_id.id)],
                                                order='punching_time desc', limit=1)
                                            if last_punch and last_punch.punch_type == '1':
                                                punch_type = '0'
                                        elif afternoon_start <= float(local_dt.hour) < afternoon_end:
                                            punch_type = '0'

                                        zk_attendance.create({
                                            'employee_id': get_user_id.id,
                                            'device_id_num': each.user_id,
                                            'attendance_type': str(each.status),
                                            'punch_type': str(punch_type),
                                            'punching_time': atten_time,
                                            'address_id': info.address_id.id
                                        })

                                        att_var = hr_attendance.search([(
                                            'employee_id', '=', get_user_id.id),
                                            ('check_out', '=', False)])

                                        if punch_type == '0':
                                            if not att_var:
                                                hr_attendance.create({
                                                    'employee_id': get_user_id.id,
                                                    'check_in': atten_time,
                                                    'is_bio_device': True
                                                })
                                            if att_var:
                                                last_punch = hr_attendance.search(
                                                    [('employee_id', '=', get_user_id.id)],
                                                    order='check_in desc', limit=1)

                                                last_punch_date = last_punch.check_in.date()
                                                atten_time_date = fields.Datetime.from_string(atten_time).date()

                                                if atten_time_date > last_punch_date:
                                                    hr_attendance.create({
                                                        'employee_id': get_user_id.id,
                                                        'check_in': atten_time,
                                                        'is_bio_device': True
                                                    })
                                        else:  # check-out
                                            if len(att_var) == 1:
                                                att_var.write({
                                                    'check_out': atten_time,
                                                    'is_bio_device': True
                                                })
                                            else:
                                                att_var1 = hr_attendance.search(
                                                    [('employee_id', '=', get_user_id.id)])
                                                if att_var1:
                                                    att_var1[-1].write({
                                                        'check_out': atten_time,
                                                        'is_bio_device': True
                                                    })
                                else:
                                    employee = self.env['hr.employee'].create({
                                        'device_id_num': each.user_id,
                                        'name': uid.name
                                    })
                                    zk_attendance.create({
                                        'employee_id': employee.id,
                                        'device_id_num': each.user_id,
                                        'attendance_type': str(each.status),
                                        'punch_type': '0',
                                        'punching_time': atten_time,
                                        'address_id': info.address_id.id
                                    })
                                    hr_attendance.create({
                                        'employee_id': employee.id,
                                        'check_in': atten_time,
                                        'is_bio_device': True
                                    })
                    conn.disconnect()
                    return True
                else:
                    raise UserError(_('Unable to get the attendance log, please try again later.'))
            else:
                raise UserError(_('Unable to connect, please check the parameters and network connections.'))


    def action_restart_device(self):
        """For restarting the device"""
        zk = ZK(self.device_ip, port=self.port_number, timeout=15,
                password=0,
                force_udp=False, ommit_ping=False)
        self.device_connect(zk).restart()
