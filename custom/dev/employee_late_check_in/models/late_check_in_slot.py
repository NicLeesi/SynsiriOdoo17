# models/late_check_in_slot.py
from odoo import models, fields

class LateCheckInSlot(models.Model):
    _name = 'late.check.in.slot'
    _description = 'Late Check-in Slot Configuration'

    name = fields.Char("Name", required=True)
    check_in_change = fields.Datetime(string="Check In change time to", default=fields.Datetime.now, required=True, tracking=True)
    note = fields.Text("Note")
