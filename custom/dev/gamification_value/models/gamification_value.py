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
    # Related One2many field: fetches all goals linked to the selected challenge
    related_goal_ids = fields.One2many(
        comodel_name='gamification.goal',
        inverse_name='challenge_id',
        string='Related Goals',
        related='challenge_id.goal_ids',
        readonly=False,
        help='Goals that are part of the selected challenge.'
    )
    # Link to HR department
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        help='The department related to this gamification value.'
    )






    # Original code
    # goal_id = fields.Char(string='Goal ID', required=True)
    # current_value = fields.Integer(string='Current Value')
    # apply_date = fields.Date("(Use in payslip compute) Apply date",help='If apply date is match payslip date update goal the value', compute="_compute_apply_date", inverse='_inverse_apply_date')
    # manual_apply_date = fields.Date(string='Manual Apply Date')



    # def _compute_apply_date(self):
    #
    #     today = datetime.today()
    #     last_month = today.month - 1 or 12
    #     year = today.year if last_month != 12 else today.year - 1
    #
    #     for record in self:
    #         if record.manual_apply_date:
    #             record.apply_date = record.manual_apply_date
    #         else:
    #             try:
    #                 record.apply_date = today.replace(month=last_month, year=year)
    #             except ValueError:
    #                 # Handle cases where the previous month has fewer days (e.g., from March 31 to February 28/29)
    #                 last_day_of_last_month = (today.replace(day=1) - timedelta(days=1)).day
    #                 record.apply_date = today.replace(day=last_day_of_last_month, month=last_month, year=year)
    #
    # @api.onchange('name')
    # def _onchange_goal_name(self):
    #     if self.name:
    #         self.goal_id = self.name.code if self.name else False
    #
    #
    #     for record in self:
    #         today = datetime.today()
    #         last_month = today.month - 1 or 12
    #         year = today.year if last_month != 12 else today.year - 1
    #
    #         try:
    #             record.apply_date = today.replace(month=last_month, year=year)
    #         except ValueError:
    #             # Handle cases where the previous month has fewer days (e.g., from March 31 to February 28/29)
    #             last_day_of_last_month = (today.replace(day=1) - timedelta(days=1)).day
    #             record.apply_date = today.replace(day=last_day_of_last_month, month=last_month, year=year)
    #
    # def _inverse_apply_date(self):
    #     for record in self:
    #         record.manual_apply_date = record.apply_date
    #
    # def action_update_goal_value(self):
    #     for record in self:
    #         if record.apply_date:
    #             goals = self.env['gamification.goal'].search([
    #                 ('state', '=', 'inprogress'),
    #                 ('start_date', '<=', record.apply_date),
    #                 ('end_date', '>=', record.apply_date)
    #             ])
    #             for goal in goals:
    #                 goal.current = record.current_value
