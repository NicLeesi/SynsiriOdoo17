/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PivotRenderer } from "@web/views/pivot/pivot_renderer";


patch(PivotRenderer.prototype, {
    /**
     * Override getFormattedValue to hide zeros
     */
    getFormattedValue(cell) {
        const result = super.getFormattedValue(cell);


        // Check if result is 0 or "0" or "0.00"
        if (result === 0 || result === '0' || result === '0.00' || result === '0.0') {
            return '';
        }

        return result;
    }
});