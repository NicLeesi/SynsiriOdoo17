
from odoo import api, fields, models

class ProgressiveRate(models.Model):

    _name = 'progressive.rate'
    _description = 'Progressive Rate IDs'


    late_check_in_progressive_rate_id = fields.Many2one('late.check.in.progressive.rate', string='Late check in progressive rate',
                                 required=True,
                                 ondelete='cascade', help="Late check in progressive rate", index=True)
    late_minute_range = fields.Integer(string='Late minutes range',help='Setting late minutes range.', required=True, store=True)
    penalty_rate = fields.Integer(string='Penalty rate for the late minute range', help='Setting multiply rate to penalty amount.')

    def _recompute_late_penalties(self):
        self.mapped('late_check_in_progressive_rate_id')._recompute_late_penalties()

    # line
    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        recs._recompute_late_penalties()
        return recs

    def write(self, vals):
        res = super().write(vals)
        self._recompute_late_penalties()
        return res

    def unlink(self):
        parents = self.mapped('late_check_in_progressive_rate_id')
        res = super().unlink()
        parents._recompute_late_penalties()
        return res
