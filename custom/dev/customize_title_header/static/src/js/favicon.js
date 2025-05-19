/** @odoo-module **/

import { registry } from "@web/core/registry";
import { WebClient } from "@web/webclient/webclient"
import {patch} from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

// Replaces Odoo in window title to My Title
patch(WebClient.prototype,  {
    setup() {
        super.setup();
        const titleService = useService("title");
        titleService.setParts({ zopenerp: "SApp" });
    },
});