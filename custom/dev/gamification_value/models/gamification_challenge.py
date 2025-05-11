from odoo import models, fields

class GamificationChallenge(models.Model):
    _inherit = 'gamification.challenge'

    goal_ids = fields.One2many('gamification.goal', 'challenge_id', string='Goals')

