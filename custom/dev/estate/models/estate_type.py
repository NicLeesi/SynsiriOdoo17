from odoo import api, fields, models, _

class Type(models.Model):
    _name = "estate.type"
    _description = "estate type"
    # _inherit = 'mail.thread'
    _order = "sequence, name, id"


    name = fields.Char(string="Property Type Id", required=True)
    property_ids = fields.One2many("estate.property", "property_type_id", string='')
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.")
    type_offer_id = fields.One2many("estate.offer", "offer_property_type_id" , string='' )
    offer_count = fields.Integer(string="Offer count", compute='compute_offer_count')

    _sql_constraints = [
        (
            'unique_tag_name',
            'UNIQUE(property_type_id)',
            'Name must be unique.'
        ),
    ]

    @api.depends('type_offer_id')
    def compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.type_offer_id)


