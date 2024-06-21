# -*- coding: utf-8 -*-
#############################################################################
# Nic Leehard Develop
#############################################################################
from odoo import models, fields


class GoalDefinition(models.Model):

    _inherit = 'gamification.goal.definition'
    _description = 'Gamification goal definition'

    # Define your fields here
    code = fields.Char(string='Code', required=True, help='For reference in payslip compute')

