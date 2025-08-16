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
    penalty_amount = fields.Float(
        compute="_compute_penalty_amount",
        store=True,
        string="Amount",
        help="Amount to deduct based on progressive rate or system config."
    )
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('approved', 'Approved'),
                                        ('refused', 'Refused'),
                                        ('deducted', 'Deducted')],
                             string="State", default="approved",
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

    @api.depends('late_minutes','employee_id')
    def _compute_penalty_amount(self):
        """Compute the penalty amount if the employee was late"""
        ICP = self.env['ir.config_parameter'].sudo()

        default_amount = float(ICP.get_param('deduction_amount') or 0)
        default_type = ICP.get_param('deduction_type') or 'minutes'

        progressive = self.env['late.check.in.progressive.rate']

        for rec in self:
            penalty = 0.0
            minutes = int(rec.late_minutes or 0)

            if rec.employee_id and minutes > 0:
                prog = progressive.search([('employee_ids', 'in', rec.employee_id.ids)],
                     order='id desc', limit=1)
                if prog and prog.progressive_rate_ids:
                    lines = (prog.progressive_rate_ids.sorted
                             (key=lambda l: l.late_minute_range or 0))
                    match = next((ln for ln in lines if minutes <= ln.late_minute_range), None)
                    if not match:
                        match = lines[-1]

                    rate = float(match.penalty_rate or 0.0)
                    penalty = minutes * rate
                else:
                    penalty = (default_amount * minutes) if default_type == 'minutes' else default_amount
            rec.penalty_amount = penalty








    # def _compute_penalty_amount(self):
    #     """Compute the penalty amount if the employee was late"""
    #     for rec in self:
    #         amount = float(self.env['ir.config_parameter'].sudo().get_param(
    #             'deduction_amount'))
    #         rec.penalty_amount = amount
    #         if self.env['ir.config_parameter'].sudo().get_param(
    #                 'deduction_type') == 'minutes':
    #             rec.penalty_amount = amount * rec.late_minutes



    def approve(self):
        """Change state to approved when approve button clicks"""
        self.state = 'approved'

    def reject(self):
        """Change state refused when refuse button clicks"""
        self.state = 'refused'
