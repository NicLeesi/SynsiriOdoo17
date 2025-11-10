from odoo import models

class GamificationGoal(models.Model):
    _inherit = 'gamification.goal'

    def action_set_to_draft(self):
        """Set goal back to draft state."""
        return self.write({'state': 'draft'})
