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
from odoo import models, api


class HrPayslip(models.Model):
    """inherited to add fields"""
    _inherit = 'hr.payslip'

    def action_payslip_done(self):
        res = super().action_payslip_done()
        employees = self.mapped('employee_id').sudo()

        # 1) Recompute paid insurance based on confirmed payslips
        #    (call your compute directly, or _compute_* if you rename it)
        employees.get_paid_insurance()

        # 2) Then recompute deduced amounts that depend on insurance_account
        employees.get_deduced_amount()
        return res

    @api.model
    def get_inputs(self, contract_ids, date_from, date_to):
        """used get inputs, to add datas"""
        res = super().get_inputs(contract_ids, date_from, date_to)
        contract_obj = self.env['hr.contract']

        for contract in contract_ids:
            contract_record = contract_obj.browse(contract.id)
            emp_id = contract_record.employee_id

            if emp_id.insurance_ids:
                for insurance in emp_id.insurance_ids:
                    insurance_policy_name = insurance.policy_id.name
                    insurance_amount = insurance.policy_amount  # Use the specific amount per policy
                    insurance_policy_code = insurance.policy_id.code

                    input_data = {
                        'name': insurance_policy_name,
                        'code': insurance_policy_code,
                        'amount': insurance_amount,
                        'contract_id': contract.id,
                    }
                    res.append(input_data)

        return res