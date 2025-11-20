from odoo import models, api, fields
import requests
import logging
import time

_logger = logging.getLogger(__name__)


class SteelPriceHistory(models.Model):
    _name = "steel.price.history"
    _description = "Steel Price History"

    name = fields.Char("Name")
    code = fields.Char("Code", index=True)
    category_name = fields.Char("Category")
    description = fields.Char("Description")
    weight = fields.Float("Weight")
    uom = fields.Char("UoM")
    price = fields.Float("Price")
    price_per_weight = fields.Float("Price per Weight")
    daily_price_change = fields.Float("Daily Change")
    weekly_price_change = fields.Float("Weekly Change")
    monthly_price_change = fields.Float("Monthly Change")
    date = fields.Datetime("Fetched On", default=fields.Datetime.now, index=True)
    price_change_display = fields.Float(
        string="Daily change p/kg(Baht)",
        compute="_compute_price_change",
        store=True,
        digits=(16, 2),
        help="Numeric difference from the previous record's price for the same item code.",
    )

    @api.depends("price", "code", "date")
    def _compute_price_change(self):
        """Compute numeric difference between this record's price and the previous record."""
        SteelPrice = self.env["steel.price.history"]
        records_by_code = {}

        # Preload records by code for efficiency
        for code in self.mapped("code"):
            if code:
                records_by_code[code] = SteelPrice.search(
                    [("code", "=", code), ("price_per_weight", "!=", 0)],
                    order="date asc"
                )

        for rec in self:
            rec.price_change_display = 0.0
            if not rec.code or rec.price is None:
                continue

            records = records_by_code.get(rec.code)
            if not records:
                continue

            ids = records.ids
            try:
                idx = ids.index(rec.id)
            except ValueError:
                continue

            if idx <= 0:
                continue

            prev = records[idx - 1]
            rec.price_change_display = round(rec.price_per_weight - (prev.price_per_weight or 0.0), 2)

    @api.model
    def fetch_prices(self):
        """Fetch steel prices from SteelBestBuy API and merge same-day records."""
        try:
            api_key = self.env["ir.config_parameter"].sudo().get_param("steelbestbuy.api_key")
            if not api_key:
                raise ValueError("API key is missing. Please set 'steelbestbuy.api_key' in System Parameters.")

            url = "https://sbb-cost.steelbestbuy.com/open-apis/products"
            headers = {
                "authority": "sbb-cost.steelbestbuy.com",
                "method": "POST",
                "path": "/open-apis/products",
                "scheme": "https",
                "accept": "*/*",
                "accept-encoding": "identity",
                "accept-language": "en-US,en;q=0.9,th;q=0.8",
                "content-type": "application/json",
                "origin": "https://steelbestbuy.com",
                "priority": "u=1, i",
                "referer": "https://steelbestbuy.com/",
                "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/142.0.0.0 Safari/537.36"
                ),
                "x-api-key": api_key,
            }

            # Steel bar and all steel
            payloads1 = [
                {
                    "productCodes": [
                        "2S4016100", "2RTT10005002.3T", "2CTC10050202.3",
                        "2CGI10050202.1F", "2PLT4806.0", "2RTG05002501.15",
                    ]
                },
                {
                    "productCodes": [
                        "2S2406100", "2S2409100", "2S4012100",
                        "2S4016100", "2S4020100", "2S4025100",
                    ]
                },
            ]

            # 90° Angle Steel
            payload2 = [
                {
                    "productCodes": [
                        "2ANG0250306", "2ANG0250506", "2ANG0300306", "2ANG0300506",
                        "2ANG0400306", "2ANG0400406", "2ANG0400506", "2ANG0400606",
                        "2ANG0500306", "2ANG0500406", "2ANG0500506", "2ANG0500606",
                        "2ANG0750606", "2ANG0750906", "2ANG0751206",
                        "2ANG1000706", "2ANG1001006", "2ANG1001206",
                    ]
                }
            ]

            # Steel Sheet
            payload4 = [
                {
                    "productCodes": [
                        "2PLT4802.0", "2PLT4803.0", "2PLT4804.0", "2PLT4804.5",
                        "2PLT4805.0", "2PLT4806.0", "2PLT4808.0", "2PLT4809.0",
                        "2PLT4810.0", "2PLT4812.0", "2PLT4815.0", "2PLT4819.0",
                        "2PLT4820.0", "2PLT4822.0", "2PLT4825.0",
                    ]
                }
            ]

            # Equal Angle & C-Channel Steel
            payload5 = [
                {
                    "productCodes": [
                        "2CHA05005.006", "2CHA07505.006", "2CHA10005.006",
                        "2CHA12506.006", "2CHA15006.506", "2CHA15009.006",
                        "2CHA18007.006", "2CHA20007.506", "2CHA20008.006",
                        "2CHA25009.006", "2CHA25011.006",
                    ]
                }
            ]

            # Square & Rectangular Tube (solid & hollow)
            payload6 = [
                {
                    "productCodes": [
                        "2SQT02502.3T", "2SQT03202.3T", "2SQT03802.3T", "2SQT03803.2T",
                        "2SQT05002.3T", "2SQT05003.2T", "2SQT07502.3T", "2SQT07503.2T",
                        "2SQT10002.3T", "2SQT10003.2T", "2SQT10004.5T", "2SQT12502.3T",
                        "2SQT12503.2T", "2SQT12504.5T", "2SQT15003.2T", "2SQT15004.5T",
                        "2SQT15006.0T", "2SQT20004.5T", "2SQT20006.0T",
                        "2RTT05002502.3T", "2RTT07503802.3T", "2RTT07503803.2T",
                        "2RTT07504502.3T", "2RTT07504503.2T", "2RTT10005002.3T",
                        "2RTT10005003.2T", "2RTT12505002.3T", "2RTT12505003.2T",
                        "2RTT12507502.3T", "2RTT12507503.2T", "2RTT12507504.5T",
                        "2RTT15005002.3T", "2RTT15005003.2T", "2RTT15007503.2T",
                        "2RTT15007504.5T", "2RTT15010003.2T", "2RTT15010004.5T",
                        "2RTT15010006.0T", "2RTT20005003.2T", "2RTT20010003.2T",
                        "2RTT20010004.5T", "2RTT20010006.0T",
                    ]
                },
                {
                    "productCodes": [
                        "2SQT03201.9F", "2SQT17509.0J", "2SQT03201.7F",
                        "2SQT03201.4F", "2SQT03201.2F", "2SQT03201.2J",
                    ]
                },
            ]

            # Rectangular Bar (GI) + Round Tube
            payload8 = [
                {
                    "productCodes": [
                        "2SQG07502.1F", "2SQG07501.3F", "2SQG03801.6F", "2SQG05001.0F",
                        "2SQG02501.25", "2SQG03801.15", "2SQG03801.65", "2SQG05001.3F",
                    ]
                },
                {
                    "productCodes": [
                        "2TUB114.302.5T", "2TUB264.706.0T", "2TUG060.503.2T",
                        "2TUB088.902.0T", "2TUB088.902.7T", "2TUB088.901.8J",
                        "2TUB139.803.2T", "2TUB033.402.3T", "2TUB027.201.25",
                        "2TUB033.401.43", "2TUB027.202.3T",
                    ]
                },
            ]

            # H-Beam, W-Flange, I-Beam
            payload10 = [
                {
                    "productCodes": [
                        # H-Beam
                        "2HBM10010006008006", "2HBM12512506509006", "2HBM15015007010006",
                        "2HBM17517507511006", "2HBM20020008012006", "2HBM25025009014006",
                        "2HBM30030010015006", "2HBM35035012019006", "2HBM40040013021006",
                        # W-Flange Beam
                        "2WFL10005005007006", "2WFL14810006009006", "2WFL15007505007006",
                        "2WFL19415006009006", "2WFL20010005508006", "2WFL24417507011006",
                        "2WFL25012506009006", "2WFL29420008012006", "2WFL30015006509006",
                        "2WFL34025009014006", "2WFL35017507011006", "2WFL39030010016006",
                        "2WFL40020008013006", "2WFL44030011018006", "2WFL45020009014006",
                        "2WFL48830011018006", "2WFL50020010016006", "2WFL58830012020006",
                        "2WFL60020011017006", "2WFL70030013024006", "2WFL80030014026006",
                        "2WFL90030016028006",
                        # I-Beam
                        "2IBM15007505509506", "2IBM20010007010006", "2IBM20015009016006",
                        "2IBM25012507512506", "2IBM25012510019006", "2IBM30015008013006",
                        "2IBM30015010018506", "2IBM30015011522006", "2IBM35015009015006",
                        "2IBM35015012024006", "2IBM40015010018006", "2IBM40015012525006",
                        "2IBM45017016224306", "2IBM45017511020006", "2IBM45017513026006",
                        "2IBM60019013025006",
                    ]
                }
            ]

            # Combine all payload groups
            payloads = (
                    payloads1 + payload2 + payload4 +
                    payload5 + payload6 + payload8 + payload10
            )

            # Fetch loop
            today = fields.Date.today()
            total_new, total_updated, total_items = 0, 0, 0

            for idx, payload in enumerate(payloads, 1):
                _logger.info("📦 Sending payload %s/%s with %s product codes",
                             idx, len(payloads), len(payload["productCodes"]))

                res = requests.post(url, headers=headers, json=payload, timeout=30)
                if res.status_code != 200:
                    _logger.error("❌ API error %s: %s", res.status_code, res.text[:300])
                    continue

                try:
                    raw = res.json()
                except Exception:
                    _logger.error("❌ Invalid JSON response for payload %s", idx)
                    continue

                items = raw.get("data", {}).get("items", [])
                if not items:
                    _logger.warning("⚠️ No items found in response for payload %s", idx)
                    continue

                priced_items = [p for p in items if p.get("price") or p.get("pricePerWeight")]
                total_items += len(priced_items)

                for item in priced_items:
                    code = item.get("code")
                    if not code:
                        continue

                    # Check for existing record from today
                    existing_today = self.search([
                        ("code", "=", code),
                        ("date", ">=", f"{today} 00:00:00"),
                        ("date", "<=", f"{today} 23:59:59"),
                    ], limit=1)

                    # Find the latest record overall for this code
                    last_record = self.search([("code", "=", code)], order="date desc", limit=1)

                    # Prepare new values from API
                    price = item.get("price")
                    price_per_weight = item.get("pricePerWeight")
                    daily_price_change = item.get("dailyPriceChange")
                    weekly_price_change = item.get("weeklyPriceChange")
                    monthly_price_change = item.get("monthlyPriceChange")

                    vals = {
                        "name": item.get("name"),
                        "category_name": item.get("categoryName"),
                        "description": item.get("description"),
                        "weight": item.get("weight"),
                        "uom": item.get("uom"),
                        "price": price,
                        "price_per_weight": price_per_weight,
                        "daily_price_change": daily_price_change,
                        "weekly_price_change": weekly_price_change,
                        "monthly_price_change": monthly_price_change,
                        "date": fields.Datetime.now(),
                    }

                    # Compare with last record to skip if unchanged
                    if last_record:
                        last_price_per_weight = last_record.price_per_weight or 0.0
                        last_daily_change = last_record.daily_price_change or 0.0
                        new_price_per_weight = price_per_weight or 0.0
                        new_daily_change = daily_price_change or 0.0

                        if (abs(last_price_per_weight - new_price_per_weight) < 0.01 and
                                abs(last_daily_change - new_daily_change) < 0.01):
                            continue

                    # Update existing or create new
                    if existing_today:
                        existing_today.write(vals)
                        total_updated += 1
                    else:
                        vals["code"] = code
                        self.create(vals)
                        total_new += 1

                _logger.info("✅ Payload %s/%s processed: %s items",
                             idx, len(payloads), len(priced_items))

                # Sleep between payloads (except after last one)
                if idx < len(payloads):
                    time.sleep(2)

            _logger.info("✅ Fetch complete: %s items total, %s updated, %s new",
                         total_items, total_updated, total_new)
            return True

        except Exception as e:
            _logger.error("❌ Fetch failed: %s", e, exc_info=True)
            raise