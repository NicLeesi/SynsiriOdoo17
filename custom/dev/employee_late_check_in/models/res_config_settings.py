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


class LateCheckinSettings(models.TransientModel):
    """Inherit the model to add fields"""
    _inherit = 'res.config.settings'

    day_off_start_morning = fields.Float(
        config_parameter='employee_late_check_in.day_off_start_morning',
        string='Day-off morning start time',
        help='Setting day-off morning start time for employee who want to work in day-off.')
    Lunch_break_time = fields.Integer(
        config_parameter='employee_late_check_in.day_off_start_afternoon',
        string='Lunch break time',
        help='Setting Lunch break time for employee.')
    late_check_in_not_count_after = fields.Char(
        config_parameter='employee_late_check_in.late_check_in_not_count_after',
        help='''When should the late check-in not count starts.If late check-in exceed the set time, 
        employee is considered absent for that period and late check-in does not count''',
        string="Late check-in not count after", )
    deduction_amount = fields.Float(
        config_parameter='employee_late_check_in.deduction_amount',
        help='How much amount need to be deducted if a employee was late ',
        string="Deduction Amount",)
    maximum_minutes = fields.Char(
        config_parameter='employee_late_check_in.maximum_minutes',
        help="Maximum time limit a employee was considered as late when compute record",
        string="Maximum Late Minute")
    late_check_in_after = fields.Char(
        config_parameter='employee_late_check_in.late_check_in_after',
        help='When should the late check-in count.',
        string="Late Check-in Starts After",)
    deduction_type = fields.Selection(
        selection=[('minutes', 'Per Minutes'), ('total', 'Per Total')],
        config_parameter='employee_late_check_in.deduction_type',
        default="minutes", string='Deduction Type',
        help='Type of deduction, (If Per Minutes is chosen then for each '
             'minutes given amount is deducted, if Per Total is chosen then '
             'given amount is deducted from the total salary)')
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id.id)

    def set_values(self):
        """Set values,
         Returns:
        :return: The result of the superclasses' set_values method.
        """
        res = super(LateCheckinSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'deduction_amount', self.deduction_amount)
        self.env['ir.config_parameter'].sudo().set_param(
            'maximum_minutes', self.maximum_minutes)
        self.env['ir.config_parameter'].sudo().set_param(
            'late_check_in_after', self.late_check_in_after)
        self.env['ir.config_parameter'].sudo().set_param(
            'deduction_type', self.deduction_type)
        self.env['ir.config_parameter'].sudo().set_param(
            'late_check_in_not_count_after', self.late_check_in_not_count_after)
        self.env['ir.config_parameter'].sudo().set_param(
            'day_off_start_morning', self.day_off_start_morning)
        self.env['ir.config_parameter'].sudo().set_param(
            'Lunch_break_time', self.Lunch_break_time)
        return res

