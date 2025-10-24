# custom/dev/project_gamification/models/project_task_gamification.py
# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProjectTask(models.Model):
    _inherit = "project.task"

    points_consumed = fields.Boolean(
        string="Importance Points Consumed",
        default=False,
        help="Marks that this task's importance points were already used in a challenge goal.",
        index=True,
    )

    @api.model
    def _get_approved_not_consumed_tasks(self):
        """Tasks eligible for the goal computation."""
        domain = [
            ("state", "=", "03_approved"),
            ("importance_type_id", "!=", False),
            ("points_consumed", "=", False),
        ]
        return self.search(domain)

    @api.model
    def _sum_importance_points_approved(self):
        """Sum points for approved & not-consumed tasks."""
        tasks = self._get_approved_not_consumed_tasks()
        # importance points are on the type
        return sum(int(t.importance_type_id.points or 0) for t in tasks)

    @api.model
    def action_consume_approved_points(self):
        """
        After goal period closes (or daily), mark approved tasks as consumed and close them.
        """
        tasks = self._get_approved_not_consumed_tasks()
        if not tasks:
            return 0
        # mark consumed
        tasks.write({"points_consumed": True})
        # optionally move to Done (state key for Done in your code is '1_done')
        to_done = tasks.filtered(lambda t: t.state == "03_approved")
        if to_done:
            to_done.write({"state": "1_done"})
        return len(tasks)
