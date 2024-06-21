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
from odoo import fields, models, _
from odoo.exceptions import UserError


class HrPayslipEmployees(models.TransientModel):
    """Create new model for Generate payslips for all selected employees"""
    _inherit = 'hr.payslip.employees'
    _description = 'Generate comslips for all selected employees'

    def action_compute_commission_sheet(self):
        """Function for compute Payslip Sheet"""
        com_payslips = self.env['hr.commission.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(
                ['date_start', 'date_end', 'credit_note'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        if not data['employee_ids']:
            raise UserError(
                _("You must select employee(s) to generate payslip(s)."))
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            com_slip_data = (
                self.env['hr.commission.payslip'].onchange_employee_id(
                    from_date, to_date, employee.id, contract_id=False))
            res = {
                'employee_id': employee.id,
                'name': com_slip_data['value'].get('name'),
                'com_struct_id': com_slip_data['value'].get('com_struct_id'),
                'contract_id': com_slip_data['value'].get('contract_id'),
                'payslip_run_id': active_id,
                'input_line_ids': [(0, 0, x) for x in
                                   com_slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in
                                         com_slip_data['value'].get(
                                             'worked_days_line_ids')],
                'employee_skill_line_ids': [(0, 0, x) for x in
                                         com_slip_data['value'].get(
                                             'employee_skill_line_ids')],
                'goal_line_ids': [(0, 0, x) for x in
                                         com_slip_data['value'].get(
                                             'goal_line_ids')],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': run_data.get('credit_note'),
                'company_id': employee.company_id.id,
            }
            com_payslips += self.env['hr.commission.payslip'].create(res)
        com_payslips.action_commission_compute_sheet()
        return {'type': 'ir.actions.act_window_close'}
