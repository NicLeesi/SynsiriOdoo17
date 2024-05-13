from odoo import api, fields, models


class InheritResUsers(models.Model):
    _name = "res.users"
    _inherit = "res.users"

    property_ids = fields.One2many("estate.property", "users_id",
    string="Real Estate Property",
    required=True,
    domain=[('date_time', '<', fields.Datetime.now()), ('state', 'in', ('New', 'Offer Received'))],
    help="Select the property for which the offer is being made."
    )
