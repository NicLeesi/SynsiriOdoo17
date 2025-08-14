# -- coding: utf-8 --
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author:  Anjhana A K (<https://www.cybrosys.com>)
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
from odoo import models, fields, api


class HrEmployee(models.Model):
    """inherited the model to add some fields"""
    _inherit = 'hr.employee'

    insurance_percentage = fields.Float(string="Company Percentage ",
                                        help="Company insurance percentage")
    deduced_amount_per_month = fields.Float(string="Salary deduced per month",
                                            compute="get_deduced_amount",
                                            help="Amount that is deduced from "
                                                 "the salary per month", store=True)
    deduced_amount_per_year = fields.Float(string="Salary deduced per year",
                                           compute="get_deduced_amount",
                                           help="Amount that is deduced from "
                                                "the salary per year", store=True)
    insurance_ids = fields.One2many('hr.insurance',
                                    'employee_id',
                                    string="Insurance", help="Insurance",
                                    domain=[('state', '=', 'active')])
    payroll_id = fields.Many2one('hr.payslip',
                                    string="payroll_id",)
    insurance_account = fields.Float(string="insurance_account",help="Total Amount that employee has paid"
                                     ,compute="get_paid_insurance")
    previous_insurance_account = fields.Float(string="Previous Insurance Account",
                                              help="Stores the previous insurance account before refund", store=False)
    insurance_fix_amount_total = fields.Float(string="Total Premium Fix Amount",
                                              compute="_compute_insurance_fix_amount_total",
                                              help="Total sum of Premium fix amounts for the employee", readonly=True)

    # @api.depends('insurance_ids.fix_amount')
    # def _compute_insurance_fix_amount_total(self):
    #     for employee in self:
    #         total_fix_amount = sum(ins.fix_amount for ins in employee.insurance_ids if ins.policy_fix_amount)
    #         employee.insurance_fix_amount_total = total_fix_amount

    @api.depends('insurance_ids.fix_amount', 'insurance_ids.state')
    def _compute_insurance_fix_amount_total(self):
        for employee in self:
            total_fix_amount = sum(
                ins.fix_amount for ins in employee.insurance_ids
                if ins.policy_fix_amount and ins.state == 'active' or 'resignation_confirm')
            employee.insurance_fix_amount_total = total_fix_amount

    @api.depends('insurance_ids', 'insurance_account')
    def get_deduced_amount(self):
        """Calculate deduced amount per month and per year"""
        current_date = fields.Date.today()
        for emp in self:
            total_yearly_amount = 0
            policy_amount = 0
            for ins in emp.insurance_ids:
                if ins.date_from:
                    if not ins.date_to or ins.date_to >= current_date:
                        if ins.state == 'active':
                            if ins.policy_coverage in ['monthly', 'permanent']:
                                if ins.policy_fix_amount:
                                    if emp.insurance_account >= ins.fix_amount:
                                        policy_amount = 0
                                    else:
                                        yearly_amount = ins.amount * 12
                                        policy_amount = yearly_amount - ((yearly_amount * emp.insurance_percentage) / 100)
                                else:
                                    yearly_amount = ins.amount * 12
                                    policy_amount = yearly_amount - ((yearly_amount * emp.insurance_percentage) / 100)
                            else:
                                yearly_amount = ins.amount
                                policy_amount = yearly_amount - ((yearly_amount * emp.insurance_percentage) / 100)

                            total_yearly_amount += policy_amount
                            ins.policy_amount = policy_amount / 12 if policy_amount else 0

                        else:
                            ins.policy_amount = policy_amount
            emp.deduced_amount_per_year = total_yearly_amount
            emp.deduced_amount_per_month = total_yearly_amount / 12 if total_yearly_amount else 0

    @api.depends('payroll_id')
    def get_paid_insurance(self):
        """Calculate the total insurance amount paid by the employee"""
        for rec in self:
            # Search for confirmed payslips of the employee
            confirmed_payslips = self.env['hr.payslip'].search([
                ('employee_id', '=', rec.id),
                ('state', '=', 'done')  # Assuming 'done' is the state for confirmed payslips
            ])

            # Get the IDs of the confirmed payslips
            confirmed_payslip_ids = confirmed_payslips.ids

            # Search for insurance input amounts related to the confirmed payslips
            insurance_amounts = self.env['hr.payslip.input'].search([
                ('payslip_id', 'in', confirmed_payslip_ids),
                ('code', '=', 'INSUR')
            ]).mapped('amount')

            insurance_return = self.env['hr.payslip.input'].search([
                ('payslip_id', 'in', confirmed_payslip_ids),
                ('code', '=', 'RIN')
            ]).mapped('amount')

            # Sum the insurance amounts
            insurance_account = sum(insurance_amounts) - sum(insurance_return)
            if insurance_account > rec.insurance_fix_amount_total:
                rec.insurance_account = rec.insurance_fix_amount_total
            else:
                rec.insurance_account = insurance_account






    # @api.depends('insurance_ids', 'insurance_account')
    # def get_deduced_amount(self):
    #     """Calculate deduced amount per month and per year"""
    #     current_date = fields.Date.today()
    #     for emp in self:
    #         ins_amount = 0
    #         for ins in emp.insurance_ids:
    #             if ins.date_from <= current_date:
    #                 if not ins.date_to or ins.date_to >= current_date:
    #                     if ins.policy_coverage in ['monthly', 'permanent']:
    #                         if ins.policy_fix_amount and emp.insurance_account >= ins.fix_amount:
    #                             ins_amount = 0
    #                             policy_amount = ins_amount - ((ins_amount * emp.insurance_percentage) / 100)
    #                         elif ins.policy_fix_amount and emp.insurance_account < ins.fix_amount:
    #                             ins_amount += ins.amount * 12
    #                         elif not ins.policy_fix_amount:
    #                             ins_amount += ins.amount * 12
    #                     else:
    #                         ins_amount += ins.amount
    #
    #         emp.deduced_amount_per_year = ins_amount - ((ins_amount * emp.insurance_percentage) / 100)
    #         emp.deduced_amount_per_month = emp.deduced_amount_per_year / 12
