# custom/dev/project_gamification/models/project_task_gamification.py
# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from typing import Optional, Union
import logging

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = "project.task"

    # Track consumption PER USER (recommended)
    consumed_by_user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="project_task_consumed_rel",
        column1="task_id",
        column2="user_id",
        string="Importance Points Consumed By",
        index=True,
        help="Users who already consumed this task's importance points.",
    )

    # # Legacy/global flag (kept only for compatibility)
    # points_consumed = fields.Boolean(
    #     string="Importance Points Consumed (Legacy)",
    #     default=False,
    #     help="Legacy boolean kept for compatibility. Per-user tracking is 'consumed_by_user_ids'.",
    #     index=True,
    # )

    # --------------------------------------
    # INTERNAL: domain + fetch
    # --------------------------------------
    @api.model
    def _eligible_points_domain(self, user_id: Optional[int]) -> list:
        """
        Eligible tasks are:
          - have importance_type_id
          - state == '1_done' (Done only)
          - assigned to user_id
          - OR (if project manager) tasks under projects they manage
          - NOT yet consumed by that user
        If user_id is falsy, return a domain that matches nothing (safety).
        """
        base = [
            ("importance_type_id", "!=", False),
            ("state", "=", "1_done"),
        ]

        if not user_id:
            # Safety: never match if user is not resolved
            base.append(("id", "=", 0))
            return base

        # --- Detect project manager role ---
        Project = self.env["project.project"].sudo()
        managed_projects = Project.search([("user_id", "=", user_id)])  # <-- change field if different

        if managed_projects:
            # Project manager: include tasks assigned to them OR under their projects
            base += [
                "|",
                ("user_ids", "in", [user_id]),
                ("project_id", "in", managed_projects.ids),
                ("consumed_by_user_ids", "not in", [user_id]),
            ]
        else:
            # Regular user: only their assigned tasks
            base += [
                ("user_ids", "in", [user_id]),
                ("consumed_by_user_ids", "not in", [user_id]),
            ]

        return base

    @api.model
    def _get_done_not_consumed_tasks(self, user_id: Optional[int]):
        """Return all done & unconsumed tasks for the given user (manager logic handled)."""
        return self.with_context(prefetch_fields=False).sudo().search(
            self._eligible_points_domain(user_id)
        )

    @api.model
    def kpi_points_for_user_id(self, user_id: int) -> float:
        """
        Strict KPI: expects a plain int user_id.
        Returns 0.0 if user_id is falsy or invalid.
        For project managers, also includes tasks in projects they manage.
        """
        try:
            uid = int(user_id)
        except Exception:
            _logger.warning("kpi_points_for_user_id called with invalid user_id=%r", user_id)
            return 0.0

        if not uid:
            return 0.0

        # --- Compute eligible tasks using updated domain logic ---
        tasks = self._get_done_not_consumed_tasks(uid)

        # --- Sum up their importance points ---
        total_points = sum(float(t.importance_type_id.points or 0.0) for t in tasks)
        return total_points

    # --------------------------------------
    # KPI API — BACKWARD-COMPAT WRAPPER
    # (If someone passes a recordset or nothing, we return 0.0 instead of leaking points)
    # --------------------------------------
    @api.model
    def kpi_sum_points_for_user(self, user: Optional[Union[int, "models.BaseModel"]] = None) -> float:
        """
        Backwards-compatible wrapper. DO NOT use in the Goal Definition.
        It returns 0.0 unless you pass a single int user_id.
        """
        # Accept explicit int; everything else is rejected → 0.0 (safety-first)
        if isinstance(user, int):
            return self.kpi_points_for_user_id(user)
        return 0.0

    # --------------------------------------
    # CONSUME API — marks the user's DONE tasks as consumed (no state flips)
    # --------------------------------------
    @api.model
    def action_consume_points_for_user(self, user_id: int) -> int:
        try:
            uid = int(user_id)
        except Exception:
            _logger.warning("action_consume_points_for_user invalid user_id=%r", user_id)
            return 0

        if not uid:
            return 0

        tasks = self._get_done_not_consumed_tasks(uid)
        if not tasks:
            return 0

        tasks.sudo().write({"consumed_by_user_ids": [(4, uid)]})
        return len(tasks)

    @api.model
    def action_consume_approved_points(self) -> int:
        return self.action_consume_points_for_user(self.env.uid)

    @api.model
    def action_consume_approved_points_cron(self) -> int:
        """
        Cron path: loop over assignees that actually have eligible DONE tasks.
        """
        Tasks = self.sudo().with_context(prefetch_fields=False)
        candidate_tasks = Tasks.search([
            ("importance_type_id", "!=", False),
            ("state", "=", "1_done"),
        ])
        if not candidate_tasks:
            return 0

        user_ids = set()
        for t in candidate_tasks:
            user_ids.update(t.user_ids.ids)

        total = 0
        for uid in user_ids:
            total += Tasks.action_consume_points_for_user(uid)
        return total
