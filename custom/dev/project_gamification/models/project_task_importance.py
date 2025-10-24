from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProjectTaskImportanceType(models.Model):
    _name = "project.task.importance.type"
    _description = "Task Importance Type"
    _order = "sequence, name"
    _rec_name = "name"

    name = fields.Char(required=True, translate=False)
    sequence = fields.Integer(default=10, index=True)
    color = fields.Integer(string="Color")
    active = fields.Boolean(default=True)
    description = fields.Text()

    _sql_constraints = [
        ("name_uniq", "unique(name)", "Importance Type name must be unique."),
    ]

    # Points used by your challenge/goal logic
    points = fields.Integer(
        string="Points",
        default=0,
        required=True,
        help="Point value awarded when this importance type is selected on a task."
    )


    @api.constrains("points")
    def _check_points_non_negative(self):
        # why: avoid accidental negative scores in gamification logic
        for rec in self:
            if rec.points is None or rec.points < 0:
                raise ValidationError(_("Points must be zero or a positive integer."))