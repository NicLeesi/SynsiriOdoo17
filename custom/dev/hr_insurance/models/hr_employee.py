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
from odoo import _, models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import pytz



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
                                     ,compute="get_paid_insurance", store=True)
    previous_insurance_account = fields.Float(string="Previous Insurance Account",
                                              help="Stores the previous insurance account before refund", store=False)
    insurance_fix_amount_total = fields.Float(string="Total Premium Fix Amount",
                                              compute="_compute_insurance_fix_amount_total",
                                              help="Total sum of Premium fix amounts for the employee", readonly=True)
    probation_status = fields.Selection(selection=[('on_probation', 'On Probation'),('pass_probation', 'Pass Probation')],
                                        string='Probation Status', default='on_probation', copy=False)
    insurance_payment_status = fields.Selection(selection=[('incomplete', 'Incomplete Insurance Payment'),
                                                           ('complete', 'Complete Insurance Payment')],
                                                            string='Insurance Payment', default='incomplete', copy=False)
    probation_bonus = fields.Float(string="Probation Bonus",help="Temporary value entered from the probation wizard.")


    def action_set_on_probation(self):
        self.write({'probation_status': 'on_probation'})

    def action_set_pass_probation(self):
        for rec in self:
            # Check if employee has at least one active insurance line with fix_amount > 0
            has_fix_line = rec.insurance_ids.filtered(
                lambda l: l.policy_fix_amount and l.fix_amount > 0 and l.state == 'active'
            )
            if not has_fix_line:
                raise UserError(_(
                    "Cannot pass probation.\n\n"
                    "Please add at least one active insurance line with a fixed amount before proceeding."
                ))
        return {
                'type': 'ir.actions.act_window',
                'res_model': 'hr.probation.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'active_ids': self.ids},
                }

    def action_set_complete_insurance_payment(self):
        self.write({'insurance_payment_status': 'complete'})

    def action_set_incomplete_insurance_payment(self):
        self.write({'insurance_payment_status': 'incomplete'})

    @api.depends('insurance_ids.fix_amount', 'insurance_ids.state')
    def _compute_insurance_fix_amount_total(self):
        for employee in self:
            total_fix_amount = sum(
                ins.fix_amount for ins in employee.insurance_ids
                if ins.policy_fix_amount and ins.state == 'active' or 'resignation_confirm')
            employee.insurance_fix_amount_total = total_fix_amount


    @api.depends(
        'insurance_ids',
        'insurance_account',
        'insurance_percentage',
        'probation_status',
        'insurance_payment_status',
    )
    def get_deduced_amount(self):
        """Calculate deduced amount per month and per year (debug version with print)"""
        current_date = datetime.today()
        for emp in self:
            total_yearly_amount = 0.0

            for ins in emp.insurance_ids:
                policy_amount = 0.0
                policy_amount_month = 0.0

                if ins.date_from and (not ins.date_to or ins.date_to >= current_date) and ins.state == 'active':
                    # yearly amount by coverage
                    if ins.policy_coverage in ('monthly', 'permanent'):
                        yearly_amount = (ins.amount or 0.0) * 12.0
                    else:
                        yearly_amount = (ins.amount or 0.0)
                    pct = emp.insurance_percentage or 0.0
                    policy_amount = yearly_amount - ((yearly_amount * pct) / 100.0)
                    policy_amount = max(policy_amount, 0.0)

                    total_yearly_amount += policy_amount
                    policy_amount_month = policy_amount / 12.0 if policy_amount else 0.0

                    # cap handling on the policy
                    if ins.policy_fix_amount:
                        insurance_account_total = (emp.insurance_account or 0.0) + policy_amount_month
                        fix_cap = ins.fix_amount or 0.0
                        if insurance_account_total >= fix_cap:
                            difference_amount = fix_cap - emp.insurance_account
                            if 'policy_amount' in ins._fields:
                                ins.policy_amount = difference_amount
                        else:
                            ins.policy_amount = policy_amount_month
                    else:
                            ins.policy_amount = policy_amount_month
                else:
                    if 'policy_amount' in ins._fields:
                        ins.policy_amount = 0.0

            emp.deduced_amount_per_year = total_yearly_amount
            emp.deduced_amount_per_month = (total_yearly_amount / 12.0) if total_yearly_amount else 0.0

    @api.depends('payroll_id', 'probation_status', 'insurance_payment_status', 'insurance_fix_amount_total', 'insurance_account')
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


            insurance_returns = self.env['hr.payslip.input'].search([
                ('payslip_id', 'in', confirmed_payslip_ids),
                ('code', '=', 'RIN')
            ]).mapped('amount')

            # 3) Base = INSUR - RIN (never below 0)
            base = max(0.0, (sum(insurance_amounts) or 0.0) - (sum(insurance_returns) or 0.0))

            # 4) Cap to fix total
            cap = rec.insurance_fix_amount_total or 0.0
            value = min(base, cap)

            # 5) Add probation bump (only if not completed)
            if rec.probation_status == 'pass_probation':
                value += rec.probation_bonus or 0.0
                rec.probation_bonus = 0
            # 6) If marked complete → force to full cap and ignore bump
            if rec.insurance_payment_status == 'complete':
                value = cap

            # 7) Set final (safe guard)
            rec.insurance_account = max(0.0, value)

            if (
                    (rec.insurance_fix_amount_total or 0.0) > 0.0
                    and (rec.insurance_account or 0.0) >= (rec.insurance_fix_amount_total or 0.0)
            ):
                rec.insurance_payment_status = 'complete'
                rec.probation_status = 'pass_probation'
            else:
                # Optional: reset if falls below cap again
                rec.insurance_payment_status = 'incomplete'



