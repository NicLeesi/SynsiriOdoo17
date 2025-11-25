/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PivotRenderer } from "@web/views/pivot/pivot_renderer";
import { onMounted, onPatched } from "@odoo/owl";

patch(PivotRenderer.prototype, {
    setup() {
        super.setup();
        const processTable = () => {
            setTimeout(() => this._processPivotTable(), 200);
        };
        onMounted(processTable);
        onPatched(processTable);
    },

    _processPivotTable() {
        const table = document.querySelector('.o_pivot table');
        if (!table) return;

        const bodyRows = table.querySelectorAll('tbody tr');

        bodyRows.forEach((row) => {
            const valueCells = row.querySelectorAll('td.o_pivot_cell_value');

            valueCells.forEach((cell) => {
                const text = cell.textContent.trim();
                const cleaned = text.replace(/[⚠️🔴❌⏰]/g, '').trim();
                const value = parseFloat(cleaned);

                // reset
                cell.style.backgroundColor = '';
                cell.style.color = '';
                cell.style.fontWeight = '';
                cell.textContent = cleaned;

                if (isNaN(value)) return;

                if (value === 0) {
                    cell.textContent = '';
                    return;
                }

                // simple rule
                if (value < 0) {
                    cell.style.backgroundColor = '#ffe6e6';
                    cell.style.color = '#cc0000';
                    cell.style.fontWeight = 'bold';
                }
            });
        });
    }
});
