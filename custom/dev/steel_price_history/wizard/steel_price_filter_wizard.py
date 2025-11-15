from odoo import models, fields, api

class SteelPriceHistoryFilterWizard(models.TransientModel):
    _name = 'steel.price.history.filter.wizard'
    _description = 'Filter Steel Price History'

    item_ids = fields.Many2many(
        'steel.price.history',
        string='Select Items',
        domain="[('price', '!=', False)]",
        help="Choose which items you want to display in the graph."
    )

    def action_view_graph(self):
        """Show full price history for selected items (same name, all dates)."""
        self.ensure_one()

        # Get distinct names from selected items
        selected_names = self.item_ids.mapped("name")

        return {
            "type": "ir.actions.act_window",
            "name": "Steel Price History Graph",
            "res_model": "steel.price.history",
            "view_mode": "graph",
            "views": [
                (self.env.ref("steel_price_history.view_steel_price_graph").id, "graph")
            ],
            # Show all records with the same name(s)
            "domain": [("name", "in", selected_names)],
            "context": {"default_name": selected_names},
        }
