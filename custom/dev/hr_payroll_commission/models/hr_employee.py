from odoo import fields, models


class HrEmployee(models.Model):
    """Inherit hr_employee for getting Payslip Counts"""
    _inherit = 'hr.employee'
    _description = 'Employee'

    com_slip_ids = fields.One2many('hr.commission.payslip',
                                   'employee_id', string='Commission Payslips',
                                   readonly=True,
                                   help="Choose Payslip for Employee")
    com_payslip_count = fields.Integer(compute='_compute_commission_payslip_count',
                                   string='Commission Payslip Count',
                                   help="Set Commission Payslip Count")

    def _compute_commission_payslip_count(self):
        """Function for count Commission Payslips"""
        com_payslip_data = self.env['hr.commission.payslip'].sudo().read_group(
            [('employee_id', 'in', self.ids)],
            ['employee_id'], ['employee_id'])
        result = dict(
            (data['employee_id'][0], data['employee_id_count']) for data in
            com_payslip_data)
        for employee in self:
            employee.com_payslip_count = result.get(employee.id, 0)