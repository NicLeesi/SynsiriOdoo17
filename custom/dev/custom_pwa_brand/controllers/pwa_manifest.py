from odoo import http
from odoo.http import request, Response
import json  # ← use stdlib json

class CustomPWAManifest(http.Controller):
    @http.route("/custom_pwa/manifest.webmanifest", type="http", auth="public", csrf=False, sitemap=False, methods=["GET"])
    def manifest(self):
        ICP = request.env["ir.config_parameter"].sudo()
        name = ICP.get_param("custom_pwa_brand.app_name", default="SApp")
        short_name = ICP.get_param("custom_pwa_brand.app_short_name", default=name)
        theme = ICP.get_param("custom_pwa_brand.theme_color", default="#714B67")
        bg = ICP.get_param("custom_pwa_brand.background_color", default="#053f9c")
        start_url = ICP.get_param("custom_pwa_brand.start_url", default="/web")
        base = "/custom_pwa_brand/static/img"

        manifest = {
            "name": name,
            "short_name": short_name,
            "start_url": start_url,
            "scope": "/",
            "display": "standalone",
            "theme_color": theme,
            "background_color": bg,
            "icons": [
                {"src": f"{base}/app-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
                {"src": f"{base}/app-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
                {"src": f"{base}/app-192-maskable.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable"},
                {"src": f"{base}/app-512-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
            ],
        }

        body = json.dumps(manifest, ensure_ascii=False)  # ← serialize here

        # Option A: Response(...)
        return Response(
            body,
            headers=[
                ("Content-Type", "application/manifest+json; charset=utf-8"),
                ("Cache-Control", "public, max-age=86400"),
                # ("Vary", "Cookie"),  # uncomment if manifest differs per user/db
            ],
        )