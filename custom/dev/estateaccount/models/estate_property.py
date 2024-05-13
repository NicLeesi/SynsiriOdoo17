from datetime import timedelta
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo import api, fields, models, Command
from odoo.exceptions import UserError, ValidationError
import logging

# class action_do_sold(models.Model):
#     _inherit = "estate.estate"
#
#     def action_do_sold_invoice(self):
#         """ When an invoice linked to a property selling registrations is
#                paid confirm . Property should indeed not be confirmed before
#                full payment. """
#         res = super(action_do_sold, self).action_do_sold_invoice()
#         raise UserError("action_do_sold_invoice accepted")
#
#         return res
#

class EstateProperty(models.Model):
    _inherit = 'estate.property'


    def action_do_sold(self):
        # Add a print statement to verify that the method is called
        # sudo().with_context(default_move_type='out_invoice')
        self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create({
              # Corresponds to 'Customer Invoice'
            'partner_id': self.partner_id.id,  # Using partner from estate.property
            "line_ids": [
                Command.create({
                    "name": self.name,
                    "quantity": "1",
                    'price_unit': self.selling_price * 0.06 + 100,
                })
            ]

        })

        # Call the super method
        return super(EstateProperty, self).action_do_sold()