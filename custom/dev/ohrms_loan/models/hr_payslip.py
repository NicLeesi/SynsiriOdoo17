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
from odoo import models


class HrPayslip(models.Model):
    """ Extends the 'hr.payslip' model to include
    additional functionality related to employee loans."""
    _inherit = 'hr.payslip'

    # def get_inputs(self, contract_ids, date_from, date_to):
    #     """Compute additional inputs for the employee payslip,
    #     considering active loans.
    #     :param contract_ids: Contract ID of the current employee.
    #     :param date_from: Start date of the payslip.
    #     :param date_to: End date of the payslip.
    #     :return: List of dictionaries representing additional inputs for
    #     the payslip."""
    #
    #     res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)
    #
    #     employee_id = self.env['hr.contract'].browse(
    #         contract_ids[0].id).employee_id if contract_ids else self.employee_id
    #
    #     loan_id = self.env['hr.loan'].search(
    #         [('employee_id', '=', employee_id.id), ('state', '=', 'approve')])
    #
    #     for loan in loan_id:
    #         for loan_line in loan.loan_lines:
    #
    #             if date_from <= loan_line.date <= date_to and not loan_line.paid:
    #
    #                 loan_found = False
    #                 for result in res:
    #
    #                     if result.get('code') == 'LO':
    #                         result['amount'] = loan_line.amount
    #                         result['loan_line_id'] = loan_line.id
    #                         loan_found = True
    #
    #                 if not loan_found:
    #                     loan_detail = loan_id.detail
    #                     # Add a new input for the loan if not found
    #                     loan_input = {
    #                         'name': loan_detail,
    #                         'code': 'LO',
    #                         'amount': loan_line.amount,
    #                         'loan_line_id': loan_line.id,
    #                         'contract_id': contract_ids[0].id
    #                     }
    #                     res.append(loan_input)
    #
    #     return res

    # nic old version not add paid LO when confirm payslip
    # def get_inputs(self, contract_ids, date_from, date_to):
    #     """Compute additional inputs for the employee payslip,
    #     considering active loans.
    #     :param contract_ids: Contract ID of the current employee.
    #     :param date_from: Start date of the payslip.
    #     :param date_to: End date of the payslip.
    #     :return: List of dictionaries representing additional inputs for
    #     the payslip."""
    #
    #     res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)
    #
    #     # Determine the employee_id either from the contract or the current payslip
    #     employee_id = self.env['hr.contract'].browse(
    #         contract_ids[0].id).employee_id if contract_ids else self.employee_id
    #
    #     # Search for approved loans for the employee
    #     loan_ids = self.env['hr.loan'].search(
    #         [('employee_id', '=', employee_id.id), ('state', '=', 'approve')])
    #
    #     total_loan_amount = 0  # Initialize the sum of loan amounts
    #     concatenated_details = ""  # Initialize an empty string to concatenate loan details
    #
    #     for loan in loan_ids:
    #         for loan_line in loan.loan_lines:
    #             # Check if the loan line date falls within the payslip period and if it's unpaid
    #             if date_from <= loan_line.date <= date_to and not loan_line.paid:
    #                 total_loan_amount += loan_line.amount  # Add the loan amount to the total
    #                 concatenated_details += loan.detail + ", "  # Concatenate each loan detail with a space
    #
    #     if total_loan_amount > 0:
    #         loan_found = False
    #         for result in res:
    #             if result.get('code') == 'LO':
    #                 result['amount'] = total_loan_amount
    #                 result[
    #                     'name'] = 'Loan: ' + concatenated_details.strip()  # Update the name with concatenated details
    #                 loan_found = True
    #
    #         if not loan_found:
    #             # Add a new input for the total loan amount with concatenated details if not found
    #             loan_input = {
    #                 'name': 'Loan(หนี้สิน): ' + concatenated_details.strip(),  # Strip to remove any trailing space
    #                 'code': 'LO',
    #                 'amount': total_loan_amount,
    #                 'contract_id': contract_ids[0].id
    #             }
    #             res.append(loan_input)
    #
    #     return res
    #
    # def action_payslip_done(self):
    #     """ Compute the loan amount and remaining amount while confirming
    #         the payslip"""
    #     super(HrPayslip, self).action_payslip_done()
    #     for line in self.input_line_ids:
    #         if line.loan_line_id:
    #             line.loan_line_id.paid = True
    #             line.loan_line_id.loan_id._compute_total_amount()
    #     return True
    #
    # def action_payslip_cancel(self):
    #     """ Compute the loan amount and remaining amount while cancel
    #         the payslip"""
    #
    #     for line in self.input_line_ids:
    #         line.loan_line_id.paid = False
    #         line.loan_line_id.loan_id._compute_total_amount()
    #
    #     return super(HrPayslip, self).action_payslip_cancel()




    def get_inputs(self, contract_ids, date_from, date_to):
        """Add unpaid loan installments for this employee as payslip inputs."""
        res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)

        # Resolve employee
        employee = self.env['hr.contract'].browse(contract_ids[0].id).employee_id if contract_ids else self.employee_id

        # Fetch all unpaid, approved loan lines in this payslip period
        loan_lines = self.env['hr.loan.line'].search([
            ('employee_id', '=', employee.id),
            ('paid', '=', False),
            ('loan_id.state', '=', 'approve'),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
        ])

        for loan_line in loan_lines:
            res.append({
                'name': ('Loan: %s') % (loan_line.loan_id.detail or loan_line.loan_id.name),
                'code': 'LO',
                'amount': loan_line.amount,
                'contract_id': contract_ids and contract_ids[0].id or False,
                'loan_line_id': loan_line.id,
                'date_from': date_from,
                'date_to': date_to,
            })
        return res

    def action_payslip_done(self):
        """Mark loan installments as paid when payslip is confirmed."""
        res = super(HrPayslip, self).action_payslip_done()
        for slip in self:
            for input_line in slip.input_line_ids:
                if input_line.loan_line_id and not input_line.loan_line_id.paid:
                    input_line.loan_line_id.write({
                        'paid': True,
                        'payslip_id': slip.id,
                    })
                    input_line.loan_line_id.loan_id._compute_total_amount()
        return res

    def action_payslip_cancel(self):
        """Unmark loan installments if payslip is cancelled."""
        for slip in self:
            for input_line in slip.input_line_ids:
                if input_line.loan_line_id and input_line.loan_line_id.paid:
                    input_line.loan_line_id.write({
                        'paid': False,
                        'payslip_id': False,
                    })
                    input_line.loan_line_id.loan_id._compute_total_amount()
        return super(HrPayslip, self).action_payslip_cancel()