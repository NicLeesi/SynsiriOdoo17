# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ChallengeLine(models.Model):
    """Gamification challenge line

    Predefined goal for 'gamification_challenge'
    These are generic list of goals with only the target goal defined
    Should only be created for the gamification.challenge object
    """
    _inherit = 'gamification.challenge.line'
    _description = 'Gamification generic goal for challenge'


    # condition = fields.Selection(string="Condition", related='definition_id.condition', readonly=True)
    code = fields.Char(string="Code", related='definition_id.code', readonly=True)


