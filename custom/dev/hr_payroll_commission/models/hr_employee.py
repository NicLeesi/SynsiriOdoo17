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

    def get_total_skill_level(self):
        total_skill_level = 0
        skill_count = 0
        skills = self.env['hr.employee.skill'].search([('employee_id', '=', self.id)])
        for skill in skills:
            skill_count += 1
            total_skill_level += skill.level_progress
        total_skill_ration = total_skill_level / skill_count

        return total_skill_ration

    def get_total_goal_completeness(self):
        total_goal_completeness = 0
        goal_count = 0
        goals = self.env['gamification.goal'].search([('employee_id', '=', self.id)])
        for goal in goals:
            goal_count += 1
            total_goal_completeness += goal.completeness
        total_goal_ration = total_goal_completeness / goal_count

        return total_goal_ration