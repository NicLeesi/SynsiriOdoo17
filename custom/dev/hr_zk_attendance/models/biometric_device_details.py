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
                        # conn.clear_attendance()
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

    # def action_download_attendance(self):
    #     """ (Original code) Function to download attendance records from the device"""
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
    #             user = conn.get_users()
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
    #                     for uid in user:
    #                         if uid.user_id == each.user_id:
    #                             get_user_id = self.env['hr.employee'].search(
    #                                 [('device_id_num', '=', each.user_id)])
    #                             if get_user_id:
    #                                 duplicate_atten_ids = zk_attendance.search(
    #                                     [('device_id_num', '=', each.user_id),
    #                                      ('punching_time', '=', atten_time)])
    #                                 if not duplicate_atten_ids:
    #                                     zk_attendance.create({
    #                                         'employee_id': get_user_id.id,
    #                                         'device_id_num': each.user_id,
    #                                         'attendance_type': str(each.status),
    #                                         'punch_type': str(each.punch),
    #                                         'punching_time': atten_time,
    #                                         'address_id': info.address_id.id
    #                                     })
    #                                     att_var = hr_attendance.search([(
    #                                         'employee_id', '=', get_user_id.id),
    #                                         ('check_out', '=', False)])
    #                                     if each.punch == 0:  # check-in
    #                                         if not att_var:
    #                                             hr_attendance.create({
    #                                                 'employee_id':
    #                                                     get_user_id.id,
    #                                                 'check_in': atten_time
    #                                             })
    #                                     if each.punch == 1:  # check-out
    #                                         if len(att_var) == 1:
    #                                             att_var.write({
    #                                                 'check_out': atten_time
    #                                             })
    #                                         else:
    #                                             att_var1 = hr_attendance.search(
    #                                                 [('employee_id', '=',
    #                                                   get_user_id.id)])
    #                                             if att_var1:
    #                                                 att_var1[-1].write({
    #                                                     'check_out': atten_time
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
    #                                     'punch_type': str(each.punch),
    #                                     'punching_time': atten_time,
    #                                     'address_id': info.address_id.id
    #                                 })
    #                                 hr_attendance.create({
    #                                     'employee_id': employee.id,
    #                                     'check_in': atten_time
    #                                 })
    #                 conn.disconnect
    #                 return True
    #             else:
    #                 raise UserError(_('Unable to get the attendance log, please'
    #                                   'try again later.'))
    #         else:
    #             raise UserError(_('Unable to connect, please check the'
    #                               'parameters and network connections.'))

    # @api.model
    # def auto_update_attendance(self):
    #     hr_attendance = self.env['hr.attendance'].search([('check_out', '=', False)])
    #
    #     for rec in hr_attendance:
    #         if rec.check_out == False:  # Assuming check_out is a datetime field
    #             # Calculate the new check_out time (5 minutes after check_in)
    #             check_in_time = fields.Datetime.from_string(rec.check_in)
    #             new_check_out_time = check_in_time + timedelta(minutes=5)
    #
    #             # Convert to UTC timezone
    #             local_tz = timezone(self.env.user.partner_id.tz or 'GMT')
    #             local_dt = local_tz.localize(new_check_out_time, is_dst=None)
    #             utc_dt = local_dt.astimezone(timezone('UTC'))
    #
    #             # Update the record
    #             rec.write({
    #                 'check_out': fields.Datetime.to_string(utc_dt)
    #             })
    #
    #     return True


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
                                                    'check_in': atten_time
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
                                                        'check_in': atten_time
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
                                        'check_in': atten_time
                                    })
                    conn.disconnect()
                    # Call auto_update_attendance method
                    # self.auto_update_attendance()
                    return True
                else:
                    raise UserError(_('Unable to get the attendance log, please try again later.'))
            else:
                raise UserError(_('Unable to connect, please check the parameters and network connections.'))

    # def action_download_attendance(self):
    #     """Function to download attendance records from the device"""
    #     _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")
    #     zk_attendance = self.env['zk.machine.attendance']
    #     hr_attendance = self.env['hr.attendance']
    #
    #     for info in self:
    #         machine_ip = info.device_ip
    #         zk_port = info.port_number
    #
    #         try:
    #             # Connecting with the device with the IP and port provided
    #             zk = ZK(machine_ip, port=zk_port, timeout=15,
    #                     password=0, force_udp=False, ommit_ping=False)
    #         except NameError:
    #             raise UserError(_("Pyzk module not found. Please install it with 'pip3 install pyzk'."))
    #
    #         conn = self.device_connect(zk)
    #
    #         if conn:
    #             conn.disable_device()  # Device cannot be used during this time
    #
    #             users = conn.get_users()
    #             attendance = conn.get_attendance()
    #
    #             if attendance:
    #                 for each in attendance:
    #                     atten_time = each.timestamp
    #                     local_tz = timezone(self.env.user.partner_id.tz or 'GMT')
    #                     local_dt = local_tz.localize(atten_time, is_dst=None)
    #                     utc_dt = local_dt.astimezone(timezone('UTC'))
    #                     atten_time = fields.Datetime.to_string(utc_dt)
    #                     date_of_atten_time = atten_time.date()
    #
    #                     for uid in users:
    #                         if uid.user_id == each.user_id:
    #                             get_user_id = self.env['hr.employee'].search([('device_id_num', '=', each.user_id)])
    #
    #                             if get_user_id:
    #                                 duplicate_atten_ids = zk_attendance.search([('device_id_num', '=', each.user_id),
    #                                                                             ('punching_time', '=', atten_time)])
    #                                 if not duplicate_atten_ids:
    #                                     # punch_type = 'check-out'  # Default to check-out
    #
    #                                     att_var = hr_attendance.search([
    #                                         ('employee_id', '=', get_user_id.id),
    #                                         ('check_out', '=', False),
    #                                         ('check_in', '>=', date_of_atten_time.strftime('%Y-%m-%d 00:00:00')),
    #                                         ('check_in', '<=', date_of_atten_time.strftime('%Y-%m-%d 23:59:59'))
    #                                     ])
    #
    #                                     att_var_full = hr_attendance.search([
    #                                         ('employee_id', '=', get_user_id.id),
    #                                         ('check_in', '>=', date_of_atten_time.strftime('%Y-%m-%d 00:00:00')),
    #                                         ('check_in', '<=', date_of_atten_time.strftime('%Y-%m-%d 23:59:59'))
    #                                     ])
    #
    #                                     if each.punch == 255 and len(att_var) == 0:
    #                                         punch_type = 'check-in'
    #                                         hr_attendance.create({
    #                                             'employee_id':
    #                                                 get_user_id.id,
    #                                             'check_in': atten_time
    #                                         })
    #
    #                                     if each.punch == 255 and len(att_var) == 1:
    #                                         last_attendance = att_var[-1]
    #                                         last_check_in_time = fields.Datetime.from_string(last_attendance.check_in)
    #                                         current_time = fields.Datetime.from_string(atten_time)
    #
    #                                         if (current_time - last_check_in_time) <= timedelta(hours=2.5):
    #                                             punch_type = 'check-in'
    #                                             hr_attendance.create({
    #                                                 'employee_id':
    #                                                     get_user_id.id,
    #                                                 'check_in': atten_time
    #                                             })
    #                                         else:
    #                                             punch_type = 'check-out'  # After 2.5 hours, consider as check-out
    #                                             hr_attendance.create({
    #                                                 'employee_id':
    #                                                     get_user_id.id,
    #                                                 'check_out': atten_time
    #                                             })
    #                                     # Always consider third timestamp as check-in
    #                                     if each.punch == 255 and len(att_var_full) == 1:
    #                                         punch_type = 'check-in'
    #                                         hr_attendance.create({
    #                                             'employee_id':
    #                                                 get_user_id.id,
    #                                             'check_in': atten_time
    #                                         })
    #
    #
    #                                     # if each.punch == 255 and len(att_var) > 1:
    #                                     #     hr_attendance.search(
    #                                     #         [('employee_id', '=', get_user_id.id), ('check_out', '=', False)])[
    #                                     #         -1].write({
    #                                     #         'check_out': atten_time
    #                                     #     })
    #                                     #
    #                                     # if each.punch == 0:
    #                                     #     hr_attendance.create({
    #                                     #         'employee_id': get_user_id.id,
    #                                     #         'check_in': atten_time
    #                                     #     })
    #
    #                                     # Check for fourth timestamp logic
    #                                     if each.punch == 255 and len(att_var) == 1 and len(att_var_full) == 1:
    #                                         punch_type = 'check-out'
    #                                         hr_attendance.create({
    #                                             'employee_id':
    #                                                 get_user_id.id,
    #                                             'check_out': atten_time
    #                                         })
    #
    #                                         # if fourth_attendance and not fourth_attendance.check_out and local_dt.hour >= 22:
    #                                         #     fourth_time = local_dt + timedelta(minutes=5)
    #                                         #     fourth_time_utc = fourth_time.astimezone(timezone('UTC'))
    #                                         #     fourth_attendance.write({
    #                                         #         'check_out': fields.Datetime.to_string(fourth_time_utc)
    #                                         #     })
    #                                         # elif len(att_var) == 3:
    #                                         #     fourth_time = local_dt + timedelta(minutes=5)
    #                                         #     fourth_time_utc = fourth_time.astimezone(timezone('UTC'))
    #                                         #     hr_attendance.create({
    #                                         #         'employee_id': get_user_id.id,
    #                                         #         'check_in': fields.Datetime.to_string(fourth_time_utc)
    #                                         #     })
    #
    #                                     # Check for fifth timestamp and beyond logic
    #                                     if each.punch == 255 and len(att_var_full) >= 2:
    #                                         punch_type = 'check-out'
    #                                         hr_attendance.create({
    #                                             'employee_id':
    #                                                 get_user_id.id,
    #                                             'check_out': atten_time
    #                                         })
    #
    #
    #                                     zk_attendance.create({
    #                                         'employee_id': get_user_id.id,
    #                                         'device_id_num': each.user_id,
    #                                         'attendance_type': str(each.status),
    #                                         'punch_type': punch_type,
    #                                         'punching_time': atten_time,
    #                                         'address_id': info.address_id.id
    #                                     })
    #
    #                             else:
    #                                 employee = self.env['hr.employee'].create({
    #                                     'device_id_num': each.user_id,
    #                                     'name': uid.name
    #                                 })
    #
    #                                 zk_attendance.create({
    #                                     'employee_id': employee.id,
    #                                     'device_id_num': each.user_id,
    #                                     'attendance_type': str(each.status),
    #                                     'punch_type': 'check-in',  # Default to check-in for new employees
    #                                     'punching_time': atten_time,
    #                                     'address_id': info.address_id.id
    #                                 })
    #
    #                                 hr_attendance.create({
    #                                     'employee_id': employee.id,
    #                                     'check_in': atten_time
    #                                 })
    #
    #                 conn.disconnect()
    #                 return True
    #
    #             else:
    #                 raise UserError(_("Unable to get the attendance log, please try again later."))
    #
    #         else:
    #             raise UserError(_("Unable to connect, please check the parameters and network connections."))

    def action_restart_device(self):
        """For restarting the device"""
        zk = ZK(self.device_ip, port=self.port_number, timeout=15,
                password=0,
                force_udp=False, ommit_ping=False)
        self.device_connect(zk).restart()
