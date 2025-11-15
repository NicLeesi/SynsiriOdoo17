{
    "name": "Steel Price History",
    "version": "1.0",
    "summary": "Fetch and record daily steel prices from SteelBestBuy API",
    "author": "NIC Workflow",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "data/steel_price_cron_data.xml",
        "views/steel_price_views.xml",
        'wizard/steel_price_filter_wizard_view.xml',
    ],
    "installable": True,
    "application": True,
}
