# -*- coding: utf-8 -*-
#############################################################################
# Nic LeeHard Develop
#############################################################################
from odoo import fields, models


class HrPayslipGoal(models.Model):
    """Create new model for adding some fields"""
    _name = 'hr.payslip.goal'
    _description = 'Payslip goal'
    _order = 'payslip_id, sequence'

    # name = fields.Char(string='Description', required=True,
    #                    help="Description for Worked Days")
    payslip_id = fields.Many2one('hr.payslip', string='PaySlip',
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
    completeness = fields.Float(string='Completeness',
                                  )
    target_goal = fields.Char(string='Target goal',
                                  )
    current = fields.Float(string='Current value',
                                  )
