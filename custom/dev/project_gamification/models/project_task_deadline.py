from datetime import datetime, timedelta
import pytz

from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    def _month_end_deadline_utc(self) -> datetime:
        """Compute last day of *current* month at 23:59:59 in user TZ, return UTC-naive.
        why: UX expects month-end in their local time; DB stores UTC.
        """
        user_tz = pytz.timezone(self.env.user.tz or "UTC")
        now_utc = fields.Datetime.now().replace(tzinfo=pytz.UTC)
        now_local = now_utc.astimezone(user_tz)

        year, month = now_local.year, now_local.month
        # first moment of next month in local tz
        if month == 12:
            next_month_local = user_tz.localize(datetime(year + 1, 1, 1, 0, 0, 0))
        else:
            next_month_local = user_tz.localize(datetime(year, month + 1, 1, 0, 0, 0))
        # last second of current month in local tz
        last_local = next_month_local - timedelta(seconds=1)
        # convert to UTC and drop tzinfo for ORM
        return last_local.astimezone(pytz.UTC).replace(tzinfo=None)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("date_deadline"):
                vals["date_deadline"] = self._month_end_deadline_utc()
        return super().create(vals_list)