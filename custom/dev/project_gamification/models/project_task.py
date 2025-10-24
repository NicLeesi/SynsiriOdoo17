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
    cover_image = fields.Image(string="Cover Image", max_width=1920, max_height=1920, store=False)

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