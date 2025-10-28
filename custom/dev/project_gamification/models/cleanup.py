from datetime import datetime, timedelta

from odoo import api, fields, models


_RETENTION_DAYS = 60        # 2 months
_BATCH_SIZE = 500             # safety: delete in chunks


class ProjectTaskImagePruner(models.AbstractModel):
    _name = "project_task_auto_prune_images.cleanup"
    _description = "Auto-delete project.task image attachments older than 60 days"

    @api.model
    def cron_purge_old_task_images(self):
        """Delete image attachments of project.task older than 60 days."""
        cutoff_dt = datetime.utcnow() - timedelta(days=_RETENTION_DAYS)
        cutoff_str = fields.Datetime.to_string(cutoff_dt)

        Att = self.env["ir.attachment"].sudo()
        Task = self.env["project.task"].sudo()

        # Narrow mimetypes to images; keep domain simple and fast.
        domain = [
            ("res_model", "=", "project.task"),
            ("create_date", "<", cutoff_str),
            ("type", "=", "binary"),
            "|",
                ("mimetype", "=ilike", "image/%"),
                ("mimetype", "=", False),  # rare/null cases; keep safe by excluding later
        ]

        # Loop in batches
        while True:
            # Fetch a batch
            batch = Att.search(domain, order="id asc", limit=_BATCH_SIZE)
            if not batch:
                break

            # Filter only real images if mimetype was missing
            real_images = batch.filtered(lambda a: (a.mimetype or "").startswith("image/"))
            if not real_images:
                # Nothing to do in this batch; advance window
                domain = [("id", ">", batch[-1].id)] + domain[1:]
                continue

            # Clear displayed_image_id on tasks that point to these attachments
            if "displayed_image_id" in Task._fields:
                tasks_pointing = Task.search([("displayed_image_id", "in", real_images.ids)])
                if tasks_pointing:
                    # why: prevent FK-like dangling pointers in UI
                    tasks_pointing.write({"displayed_image_id": False})

            # Unlink attachments (files removed from filestore)
            real_images.unlink()

            # Advance window
            domain = [("id", ">", batch[-1].id)] + domain[1:]
