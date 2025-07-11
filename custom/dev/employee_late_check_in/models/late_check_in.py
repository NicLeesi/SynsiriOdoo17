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
from odoo import api, fields, models


class LateCheckIn(models.Model):
    """Model to store late check-in records"""
    _name = 'late.check.in'
    _description = 'Late Check In'

    name = fields.Char(
        readonly=True, string='Name', help="Reference number of the record")
    employee_id = fields.Many2one('hr.employee', string="Employee",
                                  help='Late employee')
    late_minutes = fields.Integer(string="Late Minutes",
                                  help='The field indicates the number of '
                                       'minutes the worker is late.')
    date = fields.Date(string="Date", help='Current date')
    penalty_amount = fields.Float(compute="_compute_penalty_amount",
                                  help='Amount needs to be deducted',
                                  string="Amount",)
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('approved', 'Approved'),
                                        ('refused', 'Refused'),
                                        ('deducted', 'Deducted')],
                             string="State", default="draft",
                             help='State of the record')
    attendance_id = fields.Many2one('hr.attendance', string='Attendance',
                                    help='Attendence of the employee')


    def approve_all_records(self):
        """Approve all late check-in records."""
        for rec in self:
            rec.search([('state', '=', 'draft')])
            rec.state = 'approved'

    # original code
    # method that cause error!!
    # @api.model_create_multi
    # def create(self, vals_list):
    #     """Create a sequence for the model"""
    #     vals_list['name'] = self.env['ir.sequence'].next_by_code(
    #         'late.check.in') or '/'
    #     return super(LateCheckIn, self.sudo()).create(vals_list)

    # @api.model
    # def create(self, vals):
    #     # Ensure vals is treated as a dictionary
    #     if 'name' not in vals:  # Ensure 'name' is present or set a default
    #         vals['name'] = self.env['ir.sequence'].next_by_code('late.check.in.sequence')
    #
    #     return super(LateCheckIn, self).create(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' not in vals:
                vals['name'] = self.env['ir.sequence'].next_by_code('late.check.in.sequence') or '/'
        return super().create(vals_list)

    def _compute_penalty_amount(self):
        """Compute the penalty amount if the employee was late"""
        for rec in self:
            amount = float(self.env['ir.config_parameter'].sudo().get_param(
                'deduction_amount'))
            rec.penalty_amount = amount
            if self.env['ir.config_parameter'].sudo().get_param(
                    'deduction_type') == 'minutes':
                rec.penalty_amount = amount * rec.late_minutes

    def approve(self):
        """Change state to approved when approve button clicks"""
        self.state = 'approved'

    def reject(self):
        """Change state refused when refuse button clicks"""
        self.state = 'refused'
