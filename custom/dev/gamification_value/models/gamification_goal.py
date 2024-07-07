# -*- coding: utf-8 -*-
#############################################################################
# Nic Leehard Develop
#############################################################################
from odoo import models, fields, api


class Goal(models.Model):

    _inherit = 'gamification.goal'
    _description = 'Gamification goal'

    # Define your fields here
    code = fields.Char(string='Code', help='For reference in payslip')


