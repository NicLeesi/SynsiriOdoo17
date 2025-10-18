# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date

class GamificationKarmaBudget(models.Model):
    _name = 'gamification.karma.budget'
    _description = 'Monthly Karma Budget for Managers'
    _rec_name = 'manager_id'
    _order = 'month desc'

    manager_id = fields.Many2one('res.users', string='Manager', required=True)
    month = fields.Date(string='Month', default=lambda self: date.today().replace(day=1))
    monthly_limit = fields.Integer(string='Monthly Limit', required=True, default=100)
    points_used = fields.Integer(string='Points Used', default=0)
    remaining_points = fields.Integer(string='Remaining Points', compute='_compute_remaining', store=True)
    accumulate = fields.Boolean(string='Accumulate Remaining Points', default=False)

    @api.depends('monthly_limit', 'points_used')
    def _compute_remaining(self):
        for rec in self:
            rec.remaining_points = max(rec.monthly_limit - rec.points_used, 0)

    def use_points(self, amount):
        """Deduct karma points from manager's budget."""
        for rec in self:
            if rec.remaining_points < amount:
                raise ValueError("Not enough karma points remaining this month.")
            rec.points_used += amount


    @api.model
    def _cron_reset_karma_budgets(self):
        today = date.today().replace(day=1)
        for rec in self.search([]):
            if rec.accumulate:
                # carry over remaining points
                carry = rec.remaining_points
                rec.monthly_limit += carry
            # reset for new month
            rec.month = today
            rec.points_used = 0
