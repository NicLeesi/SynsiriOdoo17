from odoo import models, fields, api
from datetime import date

class GamificationKarmaDashboard(models.Model):
    _name = 'gamification.karma.dashboard'
    _description = 'Karma Dashboard'

    manager_id = fields.Many2one('res.users', string='Manager', default=lambda s: s.env.user)
    total_points = fields.Integer(string='Total Points', compute='_compute_points', store=False)
    used_points = fields.Integer(string='Used Points', compute='_compute_points', store=False)
    remaining_points = fields.Integer(string='Remaining Points', compute='_compute_points', store=False)
    employee_ids = fields.One2many('hr.employee', 'id', string='Employees', compute='_compute_employees', store=False)

    @api.onchange('manager_id')
    def _compute_points(self):
        month_start = date.today().replace(day=1)
        for rec in self:
            budget = self.env['gamification.karma.budget'].search([
                ('manager_id', '=', rec.manager_id.id),
                ('month', '=', month_start)
            ], limit=1)
            if budget:
                rec.total_points = budget.monthly_limit
                rec.used_points = budget.points_used
                rec.remaining_points = budget.remaining_points
            else:
                rec.total_points = rec.used_points = rec.remaining_points = 0

    def _compute_employees(self):
        for rec in self:
            rec.employee_ids = self.env['hr.employee'].search([])

    def action_open_employee_board(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Employee Karma Board',
            'res_model': 'hr.employee',
            'view_mode': 'tree',
            'view_id': self.env.ref('gamification_value.view_hr_employee_tree_karma').id,
            'target': 'current',
        }

    @api.model
    def open_user_dashboard(self):
        """Find or create dashboard record for current user"""
        user = self.env.user
        dashboard = self.search([('manager_id', '=', user.id)], limit=1)
        if not dashboard:
            dashboard = self.create({'manager_id': user.id})
        # force recompute before showing
        dashboard._compute_points()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Karma Dashboard',
            'res_model': 'gamification.karma.dashboard',
            'view_mode': 'form',
            'res_id': dashboard.id,
            'view_id': self.env.ref('gamification_value.view_gamification_karma_dashboard_form').id,
            'target': 'current',
        }