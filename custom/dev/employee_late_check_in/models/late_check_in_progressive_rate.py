
from odoo import api, fields, models

class LateCheckInProgressiveRate(models.Model):
    _name = 'late.check.in.progressive.rate'
    _description = 'Late Check-in Progressive Rate'

    name = fields.Char("Name", required=True)
    employee_ids = fields.Many2many('hr.employee', store=True, string='Employees')
    progressive_rate_ids = fields.One2many('progressive.rate','late_check_in_progressive_rate_id',string="Progressive Rate IDs", )
    note = fields.Text("Note")

    def _recompute_late_penalties(self):
        Late = self.env['late.check.in'].sudo()
        lates = Late.search([('employee_id', 'in', self.mapped('employee_ids').ids)])
        if lates:
            field = Late._fields['penalty_amount']
            self.env.add_to_compute(field, lates)
            lates.mapped('penalty_amount')

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        recs._recompute_late_penalties()
        return recs

    def write(self, vals):
        res = super().write(vals)
        self._recompute_late_penalties()
        return res

    def unlink(self):
        emp_ids = self.mapped('employee_ids').ids
        res = super().unlink()
        if emp_ids:
            Late = self.env['late.check.in'].sudo()
            lates = Late.search([('employee_id', 'in', emp_ids)])
            if lates:
                field = lates._fields['penalty_amount']
                self.env.add_to_compute(field, lates)
                lates.mapped('penalty_amount')
        return res
