from odoo import models, fields
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta, MO
from odoo.addons.gamification.models.gamification_challenge import start_end_date_for_period

class GamificationChallenge(models.Model):
    _inherit = 'gamification.challenge'

    goal_ids = fields.One2many('gamification.goal', 'challenge_id', string='Goals')

   
    def _generate_goals_from_challenge(self):
        """Generate the goals for each line and user.

        If goals already exist for this line and user, the line is skipped. This
        can be called after each change in the list of users or lines.
        :param list(int) ids: the list of challenge concerned"""

        Goals = self.env['gamification.goal']
        for challenge in self:
            (start_date, end_date) = start_end_date_for_period(challenge.period, challenge.start_date, challenge.end_date)
            to_update = Goals.browse(())

            for line in challenge.line_ids:
                # there is potentially a lot of users
                # detect the ones with no goal linked to this line
                date_clause = ""
                query_params = [line.id]
                if start_date:
                    date_clause += " AND g.start_date = %s"
                    query_params.append(start_date)
                if end_date:
                    date_clause += " AND g.end_date = %s"
                    query_params.append(end_date)

                query = """SELECT u.id AS user_id
                             FROM res_users u
                        LEFT JOIN gamification_goal g
                               ON (u.id = g.user_id)
                            WHERE line_id = %s
                              {date_clause}
                        """.format(date_clause=date_clause)
                self.env.cr.execute(query, query_params)
                user_with_goal_ids = {it for [it] in self.env.cr._obj}

                participant_user_ids = set(challenge.user_ids.ids)
                user_squating_challenge_ids = user_with_goal_ids - participant_user_ids
                if user_squating_challenge_ids:
                    # users that used to match the challenge
                    Goals.search([
                        ('challenge_id', '=', challenge.id),
                        ('user_id', 'in', list(user_squating_challenge_ids))
                    ]).unlink()

                values = {
                    'definition_id': line.definition_id.id,
                    'line_id': line.id,
                    'code': line.code,
                    'target_goal': line.target_goal,
                    'state': 'inprogress',
                }

                if start_date:
                    values['start_date'] = start_date
                if end_date:
                    values['end_date'] = end_date

                # the goal is initialised over the limit to make sure we will compute it at least once
                if line.condition == 'higher':
                    values['current'] = min(line.target_goal - 1, 0)
                else:
                    values['current'] = max(line.target_goal + 1, 0)

                if challenge.remind_update_delay:
                    values['remind_update_delay'] = challenge.remind_update_delay

                for user_id in (participant_user_ids - user_with_goal_ids):
                    values['user_id'] = user_id
                    to_update |= Goals.create(values)

            to_update.update_goal()

            if self.env.context.get('commit_gamification'):
                self.env.cr.commit()

        return True

