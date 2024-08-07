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
                              ('expired', 'Expired'), ],
                             default='active', string="State",
                             compute='get_status')
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, help="Company",
                                 default=lambda self: self.env.user.company_id)
    policy_amount = fields.Float(string="Policy Amount")
    code = fields.Selection([('INSUR', 'Working Insurance'),
                              ('SINS', 'Social Insurance'), ],
                             default='INSUR', string="code")

    @api.depends('policy_coverage')
    def get_status(self):
        """this function is get and set state"""
        current_date = fields.date.today()
        for rec in self:
            if rec.policy_coverage == 'monthly':
                rec.date_to = fields.Date.end_of(self.date_from, 'month')
            elif rec.policy_coverage == 'yearly':
                rec.date_to = fields.Date.end_of(self.date_from, 'year')
            elif rec.policy_coverage == 'Permanent':
                rec.date_to = False
            if rec.date_from <= current_date:
                if rec.date_to and rec.date_to >= current_date:
                    rec.state = 'active'
                else:
                    rec.state = 'expired'
