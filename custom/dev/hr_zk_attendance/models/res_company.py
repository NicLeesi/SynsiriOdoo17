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
from odoo import models, fields


class ResCompany(models.Model):
    """Inherit the model to add fields"""
    _inherit = 'res.company'

    morning_start = fields.Float(
        config_parameter='hr_zk_attendance.morning_start',
        string='Morning Start',
        help='Setting start time morning work period for employee for consider check-in or check-out.')
    morning_end = fields.Float(
        config_parameter='hr_zk_attendance.morning_end',
        string='Morning End',
        help='Setting end time morning work period for employee for consider check-in or check-out.')

    break_a_start = fields.Float(
        config_parameter='hr_zk_attendance.break_a_start',
        string='Break A Start Period',
        help='Setting Break A End period for employee for consider check-in or check-out.')
    break_a_end = fields.Float(
        config_parameter='hr_zk_attendance.break_a_end',
        string='Break A End Period',
        help='Setting Break A End period for employee for consider check-in or check-out.')

    break_b_start = fields.Float(
        config_parameter='hr_zk_attendance.break_b_start',
        string='Break B Start Period',
        help='Setting Break B start period for employee for consider check-in or check-out.')
    break_b_end = fields.Float(
        config_parameter='hr_zk_attendance.break_b_end',
        string='Break B End Period',
        help='Setting Break B End period for employee for consider check-in or check-out.')

    afternoon_start = fields.Float(
        config_parameter='hr_zk_attendance.afternoon_start',
        string='Afternoon Start',
        help='Setting start time afternoon work period for employee for consider check-in or check-out.')
    afternoon_end = fields.Float(
        config_parameter='hr_zk_attendance.afternoon_end',
        string='Afternoon End',
        help='Setting end time afternoon work period for employee for consider check-in or check-out.')

