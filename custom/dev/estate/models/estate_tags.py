from odoo import fields, models


class Tag(models.Model):
    _name = "estate.tags"
    _description = "estate tags"
    # _inherit = 'mail.thread'
    _order = "name"


    name = fields.Char(string="Tag Name", required=True)
    color = fields.Integer(string="Color")

    _sql_constraints = [
        (
            'unique_tag_name',
            'UNIQUE(name)',
            'Name must be unique.'
        ),
    ]