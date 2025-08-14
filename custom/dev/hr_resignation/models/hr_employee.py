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
                ('date_from', '>', last_approved_date)
            ]).mapped('amount')

            # Sum the insurance amounts
            rec.insurance_account = sum(insurance_amounts)

            ## create the maximum for insurance_account
            # if insurance_account > rec.insurance_fix_amount_total:
            #     rec.insurance_account = rec.insurance_fix_amount_total
            # else:
            #     rec.insurance_account = insurance_account


            # # Check resignation state
            # confirmed_resignation = self.env['hr.resignation'].search([
            #     ('employee_id', '=', rec.id),
            #     ('state', '=', 'confirm')
            # ])
            #
            # insurance_return = self.env['hr.payslip.input'].search([
            #     ('payslip_id', 'in', confirmed_payslip_ids),
            #     ('code', '=', 'RIN'),
            # ])
            #
            # if confirmed_resignation and confirmed_payslip_ids and insurance_return:
            #     rec.insurance_account = 0





    @api.depends('insurance_ids', 'insurance_account')
    def get_deduced_amount(self):
        """Calculate deduced amount per month and per year"""
        current_date = fields.Date.today()
        for emp in self:
            total_yearly_amount = 0
            for ins in emp.insurance_ids:
                if ins.date_from <= current_date:
                    if not ins.date_to or ins.date_to >= current_date:
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

                        # Check resignation state
                        confirmed_resignation = self.env['hr.resignation'].search([
                            ('employee_id', '=', emp.id),
                            ('state', '=', 'confirm')
                        ])

                        if confirmed_resignation:
                            ins.policy_amount = 0
                        else:
                            total_yearly_amount += policy_amount
                            ins.policy_amount = policy_amount / 12


            emp.deduced_amount_per_year = total_yearly_amount
            emp.deduced_amount_per_month = total_yearly_amount / 12 if total_yearly_amount else 0