from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = "project.task"

    @api.model
    def _default_user_ids(self):
        # why: Many2many default must be a recordset; single record is OK
        return self.env.user

    # Single importance per task
    importance_type_id = fields.Many2one(
        "project.task.importance.type",
        string="Importance",
        domain=[("active", "=", True)],
        index=True,
        tracking=True,
        help="Select one importance type for this task.",
          # enforce at model level
    )
    importance_color = fields.Integer(
        string="Importance Color",
        related="importance_type_id.color",
        store=False,
    )


    user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="project_task_user_rel",
        column1="task_id",
        column2="user_id",
        string="Assignees",
        context={"active_test": False},
        tracking=True,
        default=_default_user_ids,  # uses the method above
    )

    # UI-only for quick-create (click to upload)
    cover_image = fields.Image(string="Cover Image", max_width=1024, max_height=768, store=False)


    @api.model_create_multi
    def create(self, vals_list):
        # extract quick-create images first
        images = [vals.pop("cover_image", False) for vals in vals_list]
        tasks = super().create(vals_list)
        # attach after create
        for task, img in zip(tasks, images):
            if img:
                att = self.env["ir.attachment"].create({
                    "name": f"task_{task.id}_cover",
                    "res_model": "project.task",
                    "res_id": task.id,
                    "type": "binary",
                    "datas": img,  # already base64
                })
                task.displayed_image_id = att.id
        return tasks

        # Helper: True when user is a Project User but NOT a Project Manager

    @api.model
    def _is_project_user_only(self) -> bool:
        return (
                self.user_has_groups("project.group_project_user")
                and not self.user_has_groups("project.group_project_manager")
        )

    # Validation (fires on create/write and rolls back if violated)
    @api.constrains("state")
    def _check_done_for_project_user(self):
        if self._is_project_user_only():
            for rec in self:
                if rec.state == '1_done':
                    raise ValidationError(_("You are not allowed to set tasks to Done."))

    # Optional: also block at write-time (gives immediate error)
    @api.model
    def write(self, vals):
        # If user tries to change the stage_id and is not a manager
        if 'state' in vals and not self.env.user.has_group('project.group_project_manager'):
            raise ValidationError(_("You are not allowed to change the stage."))
        return super().write(vals)


    def action_set_cover_image(self):
        """Open a popup window like the default Odoo 'Set Cover Image'."""
        self.ensure_one()
        return {
            'name': 'Set a Cover Image',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.cover.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_task_id': self.id},
        }

    def action_open_chatter_upload(self):
        """Open the same multi-file upload popup as the chatter paperclip."""
        self.ensure_one()
        return {
            "type": "ir.actions.client",
            "tag": "mail.attachment_upload",  # ← this is the native Odoo uploader tag
            "context": {
                "default_res_model": "project.task",
                "default_res_id": self.id,
            },
        }