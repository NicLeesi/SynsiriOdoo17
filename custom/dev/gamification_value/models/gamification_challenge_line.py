# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ChallengeLine(models.Model):
    """add code filed to Gamification challenge line ids
    """
    _inherit = 'gamification.challenge.line'
    _description = 'Gamification generic goal for challenge'


    code = fields.Char(string="Code", related='definition_id.code')


