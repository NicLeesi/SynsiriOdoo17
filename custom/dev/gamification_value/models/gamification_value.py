# -*- coding: utf-8 -*-
#############################################################################
# Nic Lee Hard Develop
#############################################################################
from odoo import models, fields, api
from datetime import datetime, timedelta

class GamificationValue(models.Model):
    _name = 'gamification.value'
    _description = 'Gamification Value'



    # Link this record to a specific gamification challenge
    challenge_id = fields.Many2one(
        'gamification.challenge',
        string='Challenge',
        required=True,
        help='The gamification challenge this value is related to.'
    )

    goal_ids = fields.One2many(
        'gamification.goal',
        compute='_compute_goal_ids',
        string='Goals',
        readonly=False,  # allow editing
        store=False
    )

    # Link to HR department
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        help='The department related to this gamification value.'
    )

    parent_department_id = fields.Many2one(
        'hr.department',
        string='Parent Department',
        related='department_id.parent_id',
        store=True,
    )

    @api.onchange('challenge_id')
    def _onchange_challenge_id(self):
        if self.challenge_id:
            self.goal_ids = self.env['gamification.goal'].search([
                ('challenge_id', '=', self.challenge_id.id),
                ('state', '=', 'inprogress')
            ])
        else:
            self.goal_ids = False

    @api.depends('challenge_id')
    def _compute_goal_ids(self):
        for rec in self:
            rec.goal_ids = self.env['gamification.goal'].search([
                ('challenge_id', '=', rec.challenge_id.id),
                ('state', '=', 'inprogress')
            ])

    # @api.model
    # def _group_expand_parent_department_id(self, departments, domain, order):
    #     return self.env['hr.department'].search([], order=order)