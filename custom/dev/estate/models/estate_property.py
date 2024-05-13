from datetime import timedelta

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError, ValidationError



class Property(models.Model):
    # _logger = logging.getLogger(__name__)
    _name = "estate.property"
    _description = "estate record"
    # _inherit = 'mail.thread'
    _order = "id desc"



    name = fields.Char(string=_("Name"), required=True )
    expected_price = fields.Float(string="Expect Price (Baht)", default=10)
    Pool_house = fields.Boolean(string="Swimming Pool")
    garden_is_check = fields.Boolean(string="Garden", default=False)
    garden_area = fields.Integer(string="Garden Area (sqm)", default=0)
    garden_oriented = fields.Selection([('North', 'North'), ('South', 'South'), ('West', 'West'), ('East', 'East')],string="Garden Orientation")
    date_time = fields.Datetime(string="Available Date", copy=False,default=fields.Date.add(fields.Datetime.now(), months=3))
    selling_price = fields.Float(string="Selling Price", readonly=True)
    bed_room = fields.Integer(string="Bed Rooms", default=2)
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection([('New','New'), ('Offer Received','Offer Received'), ('Offer Accepted','Offer Accepted'),('Sold','Sold'), ('Canceled','Canceled')],string="Status", required=True, copy=False, default='New')
    living_area = fields.Integer(string="Living Area (sqm)", default=0)

    total_area = fields.Integer(string="Total Area (sqm)", compute='_compute_total_area')
    partner_id = fields.Many2one("res.partner", string="Buyer", copy=False )
    users_id = fields.Many2one("res.users", string="Sale man", default=lambda self: self.env.user)
    tag_ids = fields.Many2many("estate.tags", string="tags",)
    offer_ids = fields.One2many("estate.offer", 'property_id', string='')
    best_offer = fields.Float(string="Best Offer", compute='_compute_best_offer')
    property_type_id = fields.Many2one("estate.type", required=True)

    _sql_constraints = [
        ('unique_name',
         'UNIQUE(name)',
         'Name must be unique.'
         ),


    ]


    @api.ondelete(at_uninstall=False)
    def _unlink_if_not_new_canceled(self):
            if self.state not in ("New","Canceled") :
                raise ValidationError("can only delete New or Canceled property ")

    @api.constrains('expected_price')
    def _check_expected_price(self):
        for record in self:
            if float_compare(record.expected_price, 0, precision_digits=2) <= 0:
                raise ValidationError("Expected price must be positive.")

            if float_is_zero(record.selling_price,precision_digits=2) == 0:
                raise ValidationError("Selling price already set.")

    @api.constrains('selling_price')
    def _check_selling_price(self):
        for record in self:
            if record.selling_price < 0:
                raise ValidationError("Selling price must be positive.")
            if record.selling_price != 0 and record.selling_price < record.expected_price * 0.9:
                raise ValidationError("Selling price must be at least 90% of the expected price.")

    @api.depends('garden_area', 'living_area')
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.garden_area + record.living_area

    @api.depends('offer_ids.offer_price')
    def _compute_best_offer(self):
        for record in self:
            if record.offer_ids:
                record.best_offer = max(record.offer_ids.mapped('offer_price'))
            else:
                record.best_offer = 0  # Or any other default value you prefer

    @api.onchange('garden_is_check')
    def _onchange_garden_is_check(self):
        if self.garden_is_check:
            self.garden_area = 10
            self.garden_oriented = 'North'
        else:
            self.garden_area = 0
            self.garden_oriented = ''

    def action_do_sold(self):
        for record in self:
            if record.state == 'Offer Accepted':
                record.state = 'Sold'
            else:
                raise UserError("No offer accepted")
        return True

    def action_do_cancel(self):
        for record in self:
            if record.state == 'Sold':
                raise UserError("Has been Canceled ")
            else:
                record.state = 'Canceled'
        return True


class Offer(models.Model):
    _name = "estate.offer"
    _description = "estate offer"
    _order = "offer_price desc"
    # _inherit = 'mail.thread'


    offer_price = fields.Float(string="Offer Price", required=True)
    offer_status = fields.Selection(
        [('Accepted', 'Accepted'), ('Refused', 'Refused')], string="Offer Status", copy=False)
    Offer_partner_id = fields.Many2one("res.partner", string="Partner", required=True)
    property_id = fields.Many2one("estate.property", required=True)
    fallback_date = fields.Date(string="Create Date", copy=False,
                                default=fields.Date.today())
    validity = fields.Integer(string="Validity", default=7 )
    date_deadline = fields.Date(string="Date Deadline", copy=False,compute='_compute_date_deadline', inverse="_inverse_date_deadline")
    offer_price_is_check = fields.Boolean(string="Offer Check", default=False)

    offer_property_type_id = fields.Many2one(
        'estate.type',
        string='Property Type',
        related='property_id.property_type_id',
        store=True
    )


    @api.model
    def create(self, vals):
        if self.env['estate.property'].browse(vals['property_id']):
            self.env['estate.property'].browse(vals['property_id']).state = 'Offer Received'
        return super().create(vals)


    @api.constrains('offer_price')
    def _check_offer_price_lower_90percent(self):
        for record in self:
            if record.offer_price < record.property_id.expected_price * 0.9:
                raise ValidationError("Offer price must be at least 90% of the expected price.")


    @api.depends('validity','date_deadline')
    def _compute_date_deadline(self):
        for record in self:
            record.date_deadline = record.fallback_date + timedelta(days=record.validity)

    def _inverse_date_deadline(self):
        for record in self:
            fallback_date = fields.Date.from_string(record.fallback_date)
            date_deadline = fields.Date.from_string(record.date_deadline)
            time_different = date_deadline - fallback_date
            record.validity = time_different.days

    def Price_offer_accept(self):
        for record in self:
            record.offer_status = 'Accepted'
            record.property_id.partner_id = record.Offer_partner_id
            record.property_id.selling_price = record.offer_price
            record.property_id.state = 'Offer Accepted'
        return True

    def Price_offer_refuse(self):
        for record in self:
            record.offer_status = 'Refused'
            record.property_id.selling_price = 0
            record.property_id.state = 'New'
        return True

    @api.constrains('offer_status', 'property_id')
    def _check_accepted_offer(self):
        for offer in self:
            if offer.offer_status == 'Accepted':
                accepted_offers = self.search(
                    [('offer_status', '=', 'Accepted'), ('property_id', '=', offer.property_id.id)])
                if len(accepted_offers) > 1 or (len(accepted_offers) == 1 and accepted_offers[0] != offer):
                    raise ValidationError("Only one offer can be accepted for a given property.")