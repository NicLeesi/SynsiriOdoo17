from odoo import api, fields, models
from datetime import date, timedelta

class GamificationChallenge(models.Model):
    _inherit = "gamification.challenge"

    @api.model
    def _update_all(self):
        """Update all challenges and goals, even for inactive users."""
        if not self:
            return True

        Goals = self.env["gamification.goal"]
        yesterday = fields.Date.to_string(date.today() - timedelta(days=1))

        # 🔸 Custom SQL: no join with bus_presence
        self.env.cr.execute("""
            SELECT gg.id
              FROM gamification_goal AS gg
             WHERE gg.closed IS NOT TRUE
               AND gg.challenge_id IN %(challenge_ids)s
               AND (gg.state = 'inprogress'
                    OR (gg.state = 'reached' AND gg.end_date >= %(yesterday)s))
          GROUP BY gg.id
        """, {
            "challenge_ids": tuple(self.ids),
            "yesterday": yesterday,
        })

        # same as base method from here onward
        Goals.browse(goal_id for [goal_id] in self.env.cr.fetchall()).update_goal()

        self._recompute_challenge_users()
        self._generate_goals_from_challenge()

        for challenge in self:
            if challenge.last_report_date != fields.Date.today():
                if challenge.next_report_date and fields.Date.today() >= challenge.next_report_date:
                    challenge.report_progress()
                else:
                    closed_goals_to_report = Goals.search([
                        ("challenge_id", "=", challenge.id),
                        ("start_date", ">=", challenge.last_report_date),
                        ("end_date", "<=", challenge.last_report_date),
                    ])
                    if closed_goals_to_report:
                        challenge.report_progress(subset_goals=closed_goals_to_report)

        self._check_challenge_reward()
        return True
