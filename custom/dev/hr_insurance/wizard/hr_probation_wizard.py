from odoo import models, fields, api

class HrProbationWizard(models.TransientModel):
    _name = 'hr.probation.wizard'
    _description = 'add extra value for insurance accout after pass probation'

    probation_paid_insurance = fields.Float(string='Paid Amount', required=True, help='Insurace Amount that has pay before pass probation for adding in insurance account' )


    def action_confirm(self):
        """Apply wizard value to employee and trigger recomputation"""
        active_ids = self.env.context.get('active_ids', [])
        employees = self.env['hr.employee'].browse(active_ids)

        for rec in employees:
            rec.probation_bonus = self.probation_paid_insurance
            rec.probation_status = 'pass_probation'

        return {'type': 'ir.actions.act_window_close'}