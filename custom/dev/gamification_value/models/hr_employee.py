# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import date

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    karma_points = fields.Integer(
        string='Karma (User)',
        compute='_compute_karma_points',
        store=False,
        help='Karma points of the linked user account.'
    )

    manager_remaining_points = fields.Char(
        string="Manager Points Display",
        compute="_compute_manager_points_display",
        store=False
    )

    pending_karma = fields.Integer(
        string="Pending Karma",
        help="Temporary karma points before saving.",
    )
    applied = fields.Boolean(string="Applied", default=False)

    karma_received = fields.Integer(
        string='Karma Received',
        compute='_compute_karma_received',
        store=False,
        help='Total Karma points received by this employee (based on linked user).'
    )

    rank_id = fields.Many2one(
        related='user_id.rank_id',
        string="Karma Rank",
        store=True,  # <-- IMPORTANT
        readonly=True,
    )

    badge_ids = fields.One2many(
        comodel_name='gamification.badge.user',
        inverse_name='user_id',
        string='Badges',
        related='user_id.badge_ids',
        store=False,
    )
    @api.depends('user_id.karma')
    def _compute_karma_received(self):
        for emp in self:
            emp.karma_received = emp.user_id.karma if emp.user_id else 0

    @api.depends('user_id')
    def _compute_manager_points_display(self):
        user = self.env.user
        month_start = date.today().replace(day=1)
        budget = self.env['gamification.karma.budget'].search([
            ('manager_id', '=', user.id),
            ('month', '=', month_start)
        ], limit=1)

        for emp in self:
            if budget:
                emp.manager_remaining_points = f"{budget.remaining_points} / {budget.monthly_limit}"
            else:
                emp.manager_remaining_points = "0 / 0"


    @api.depends('user_id')
    def _compute_karma_points(self):
        for emp in self:
            emp.karma_points = emp.user_id.karma if emp.user_id else 0

    def action_add_karma(self):
        manager_user = self.env.user
        today = date.today()
        first_day = today.replace(day=1)

        # find or create monthly budget
        budget = self.env['gamification.karma.budget'].search([
            ('manager_id', '=', manager_user.id),
            ('month', '=', first_day)
        ], limit=1)


        # check if enough remaining points before adding
        if budget.remaining_points < 10:
            raise UserError(
                f"You don’t have enough karma points left this month.\n"
                f"Remaining: {budget.remaining_points}"
            )

        for emp in self:
            if not emp.user_id:
                raise UserError(
                    f"Employee '{emp.name}' is not linked to any user. "
                    f"Please set a user before giving karma points."
                )

            # if passes all checks, increase pending karma
            emp.pending_karma += 10
            emp.applied = False

        # temporarily deduct from manager’s remaining points (optional)
        budget.remaining_points -= 10
        budget.points_used += 10
        return {
            'effect': {
                'fadeout': 'slow',
                'message': f'+10 Karma added successfully!',
                'type': 'rainbow_man',
            }
        }

    def action_subtract_karma(self):
        manager_user = self.env.user
        today = date.today()
        first_day = today.replace(day=1)

        # Locate current manager's monthly budget
        budget = self.env['gamification.karma.budget'].search([
            ('manager_id', '=', manager_user.id),
            ('month', '=', first_day)
        ], limit=1)

        if not budget:
            raise UserError("You don't have an active karma budget this month.")

        total_returned = 0  # track how many points are restored

        for emp in self:
            if not emp.user_id:
                raise UserError(
                    f"Employee '{emp.name}' is not linked to any user. "
                    f"Cannot subtract karma points."
                )

            # ✅ Only allow subtract if there is something in pending_karma
            if emp.pending_karma <= 0:
                raise UserError(
                    f"Employee '{emp.name}' has no pending karma points to subtract."
                )

            # determine how much we’re subtracting (e.g., 10 or whatever remains)
            subtract_amount = min(10, emp.pending_karma)

            emp.pending_karma -= subtract_amount
            emp.applied = False

            # return those points to manager
            budget.remaining_points += subtract_amount
            budget.points_used = max(budget.points_used - subtract_amount, 0)
            total_returned += subtract_amount

        # ✅ Return a nicer visual confirmation (no reload)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': f'✨ {total_returned} Karma points returned to your pool!',
                'img_url': '/web/static/img/smile.svg',
                'type': 'rainbow_man',
            }
        }

    def apply_karma_changes(self):
        manager_user = self.env.user
        today = date.today()
        first_day = today.replace(day=1)

        # find the current month's karma budget for the manager
        budget = self.env['gamification.karma.budget'].search([
            ('manager_id', '=', manager_user.id),
            ('month', '=', first_day)
        ], limit=1)

        if not budget:
            raise UserError("No karma budget found for this month.")

        affected_users = self.env['res.users']

        for emp in self:
            if emp.pending_karma > 0:
                if budget.remaining_points < emp.pending_karma:
                    raise UserError(
                        f"Not enough remaining points to give {emp.pending_karma} to {emp.name}."
                    )
                if not emp.user_id:
                    raise UserError(f"{emp.name} has no linked user.")

                # update user's karma safely
                user = emp.user_id.sudo()
                user.karma += emp.pending_karma
                affected_users |= user

                # deduct from budget
                budget.sudo().remaining_points -= emp.pending_karma

                # mark employee record as updated
                emp.pending_karma = 0
                emp.applied = True

        # recompute rank for all affected users
        if affected_users:
            affected_users.sudo()._recompute_rank()

        # refresh employees’ related rank fields
        self.env['hr.employee'].invalidate_model(['rank_id'])

        # force reload view so changes appear instantly
        return {'type': 'ir.actions.client', 'tag': 'reload'}