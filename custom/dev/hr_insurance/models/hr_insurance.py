# -- coding: utf-8 --
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author:  Anjhana A K(<https://www.cybrosys.com>)
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models, api


class HrInsurance(models.Model):
    """created a new model for employee insurance"""
    _name = 'hr.insurance'
    _description = 'HR Insurance'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  required=True, help="Employee")
    policy_id = fields.Many2one('insurance.policy',
                                string='Policy', required=True, help="Policy")
    amount = fields.Float(string='Premium', required=True, help="Policy amount")
    sum_insured = fields.Float(string="Sum Insured", required=True,
                               help="Insured sum")
    policy_coverage = fields.Selection([('monthly', 'Monthly'),
                                        ('yearly', 'Yearly'),
                                        ('permanent', 'Permanent')],
                                       required=True, default='permanent',
                                       string='Policy Coverage',
                                       help="During of the policy(If blank mean permanent period")
    policy_fix_amount = fields.active = fields.Boolean('Policy Fix Amount', default=True, help="check for fix premium amount")
    fix_amount = fields.Float(string='Fix Amount', help="Total amount for Premium payable")

    date_from = fields.Date(string='Date From',
                            default=fields.date.today(),
                            help="Start date")
    date_to = fields.Date(string='Date To', help="End date")
    state = fields.Selection([('active', 'Active'),
                              ('expired', 'Expired'),
                              ('resignation_confirm', 'Resignation Confirm')],
                             default='active', string="State",
                             compute='get_status',  store=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, help="Company",
                                 default=lambda self: self.env.user.company_id)
    policy_amount = fields.Float(string="Policy Amount")


    # @api.depends('policy_coverage','resignation_id')
    # def get_status(self):
    #     """this function is get and set state"""
    #     current_date = fields.date.today()
    #
    #     for rec in self:
    #         confirmed_resignation = self.env['hr.resignation'].search([
    #             ('employee_id', '=', rec.id),
    #             ('state', '=', 'confirm')
    #         ])
    #         last_approved_revealing_date = self.env['hr.resignation'].search([
    #             ('employee_id', '=', rec.id)
    #         ], order='approved_revealing_date desc', limit=1)
    #         if last_approved_revealing_date:
    #             last_approved_date = last_approved_revealing_date.approved_revealing_date
    #         else:
    #             last_approved_date = False
    #
    #         if rec.policy_coverage == 'monthly':
    #             rec.date_to = fields.Date.end_of(self.date_from, 'month')
    #         elif rec.policy_coverage == 'yearly':
    #             rec.date_to = fields.Date.end_of(self.date_from, 'year')
    #         elif rec.policy_coverage == 'Permanent':
    #             rec.date_to = False
    #
    #         # Determine the state of the insurance
    #         if rec.date_from <= current_date:
    #             if not rec.date_to or rec.date_to >= current_date:
    #                 rec.state = 'active'
    #                 if confirmed_resignation:
    #                     rec.state = 'resignation_confirm'
    #                 if last_approved_date and rec.date_from <= last_approved_date:
    #                     rec.state = 'expired'
    #         else:
    #             rec.state = 'expired'

    @api.depends('policy_coverage', 'date_from')
    def get_status(self):
        """This function gets and sets the state."""
        current_date = fields.Date.today()

        for rec in self:

            confirmed_resignation = self.env['hr.resignation'].search([
                ('employee_id.name', '=', rec.employee_id.name),
                ('state', '=', 'confirm')
            ])

            last_approved_revealing_date = self.env['hr.resignation'].search([
                ('employee_id.name', '=', rec.employee_id.name),
                ('state', '=', 'approved')
            ], order='approved_revealing_date desc', limit=1)

            if last_approved_revealing_date:
                last_approved_date = last_approved_revealing_date.approved_revealing_date
            else:
                last_approved_date = False
            if rec.policy_coverage == 'monthly':
                rec.date_to = fields.Date.end_of(rec.date_from, 'month')
            elif rec.policy_coverage == 'yearly':
                rec.date_to = fields.Date.end_of(rec.date_from, 'year')
            elif rec.policy_coverage == 'Permanent':
                rec.date_to = False

            # Determine the state of the insurance
            if rec.date_from <= current_date:
                if not rec.date_to or rec.date_to >= current_date:
                    rec.state = 'active'
                    if last_approved_date and rec.date_from <= last_approved_date:
                        rec.state = 'expired'
                    if confirmed_resignation and not rec.state == 'expired':
                        rec.state = 'resignation_confirm'
                else:
                    rec.state = 'expired'
            else:
                rec.state = 'active'