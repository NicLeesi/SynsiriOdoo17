# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models, api


class HrEmployee(models.Model):
    """
    Extends the 'hr.employee' model to include additional fields related to
    employee resignation.
    """
    _inherit = 'hr.employee'

    resign_date = fields.Date('Resign Date', readonly=True,
                              help="Date of the resignation")
    resigned = fields.Boolean(string="Resigned", default=False,
                              help="If checked then employee has resigned")
    fired = fields.Boolean(string="Fired", default=False,
                           help="If checked then employee has fired")
    resignation_ids = fields.One2many(
    'hr.resignation',
    'employee_id',
    string="Resignations",
    help="List of resignation requests for this employee",
)

    @api.depends('payroll_id')
    def get_paid_insurance(self):
        """Calculate the total insurance amount paid by the employee and return to employee"""

        for rec in self:
            # Search for confirmed payslips of the employee
            last_approved_revealing_date = self.env['hr.resignation'].search([
                ('employee_id', '=', rec.id)
            ], order='approved_revealing_date desc', limit=1)
            if last_approved_revealing_date:
                last_approved_date = last_approved_revealing_date.approved_revealing_date
            else:
                last_approved_date = '1900-01-01'


            confirmed_payslips = self.env['hr.payslip'].search([
                ('employee_id', '=', rec.id),
                ('state', '=', 'done'),  # Assuming 'done' is the state for confirmed payslips
                ('date_from', '>', last_approved_date)
            ])

            # Get the IDs of the confirmed payslips
            confirmed_payslip_ids = confirmed_payslips.ids

            # Search for insurance input amounts related to the confirmed payslips
            insurance_amounts = self.env['hr.payslip.input'].search([
                ('payslip_id', 'in', confirmed_payslip_ids),
                ('code', '=', 'INSUR'),
                ('payslip_id.date_from', '>', last_approved_date)
            ]).mapped('amount')

            insurance_returns = self.env['hr.payslip.input'].search([
                ('payslip_id', 'in', confirmed_payslip_ids),
                ('code', '=', 'RIN'),
                ('payslip_id.date_from', '>', last_approved_date)
            ]).mapped('amount')

            # 3) Base = INSUR - RIN (never below 0)
            base = max(0.0, (sum(insurance_amounts) or 0.0) - (sum(insurance_returns) or 0.0))

            # 4) Cap to fix total
            cap = rec.insurance_fix_amount_total or 0.0
            value = min(base, cap)

            # 5) Add probation bump (only if not completed)
            if rec.probation_status == 'pass_probation' and rec.insurance_fix_amount_total:
                value += 1000.0

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


    @api.depends('insurance_ids', 'insurance_account', 'resignation_ids.state')
    def get_deduced_amount(self):
        """
        Extend insurance logic to consider resignation confirmation.
        If resignation is confirmed, zero all insurance deductions.
        """
        super(HrEmployee, self).get_deduced_amount()
        current_date = fields.Date.today()

        for emp in self:
            # Check for confirmed resignation
            confirmed_resignation = self.env['hr.resignation'].search([
                ('employee_id', '=', emp.id),
                ('state', '=', 'confirm')
            ], limit=1)

            if confirmed_resignation:
                for ins in emp.insurance_ids:

                    # Only modify active policies
                    if ins.state == 'active' and (not ins.date_to or ins.date_to >= current_date) and ins.policy_id.code == 'INSUR' :
                        ins.policy_amount = 0.0

                # Reset deductions
                emp.deduced_amount_per_month = 0.0
                emp.deduced_amount_per_year = 0.0





