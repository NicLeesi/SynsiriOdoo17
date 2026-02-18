# -*- coding: utf-8 -*-
#############################################################################
# Nic LeeHard Develop
#############################################################################
from odoo import fields, models


class HrComPayslipGoal(models.Model):
    """Create new model for adding some fields"""
    _name = 'hr.commission.payslip.goal'
    _description = 'Commission Payslip goal'
    _order = 'com_payslip_id, sequence'

    # name = fields.Char(string='Description', required=True,
    #                    help="Description for Worked Days")
    com_payslip_id = fields.Many2one('hr.commission.payslip', string='Commission PaySlip',
                                 required=True,
                                 ondelete='cascade', index=True,
                                 help="Choose Commission Payslip for skill")
    sequence = fields.Integer(required=True, index=True, default=10,
                              string="Sequence",
                              help="Sequence for goal")
    code = fields.Char(required=True, string="Code",
                       help="The code that can be used in the salary rules")

    definition_id = fields.Char(string='Goal name',
                                  )
    completeness = fields.Float(string='Completeness', digits=(16, 2)
                                  )
    target_goal = fields.Char(string='Target goal',
                                  )
    current = fields.Float(string='Current value'
                                  )

    # number_of_days = fields.Float(string='Number of Days',
    #                               help="Number of days worked")
    # number_of_hours = fields.Float(string='Number of Hours',
    #                                help="Number of hours worked")
    # contract_id = fields.Many2one('hr.contract', string='Contract',
    #                               required=True,
    #                               help="The contract for which applied"
    #                                    "this input")
