/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PivotRenderer } from "@web/views/pivot/pivot_renderer";
import { onMounted, onPatched } from "@odoo/owl";

console.log("Loading pivot cell coloring - simple version...");

patch(PivotRenderer.prototype, {
    setup() {
        super.setup();

        const processTable = () => {
            setTimeout(() => {
                this._processPivotTable();
            }, 200);
        };

        onMounted(processTable);
        onPatched(processTable);
    },

    _processPivotTable() {
        console.log("Processing pivot table...");

        const table = document.querySelector('.o_pivot table');
        if (!table) {
            console.log("No pivot table found");
            return;
        }

        // Get all value cells
        const cells = table.querySelectorAll('tbody td.o_pivot_cell_value');
        console.log("Found", cells.length, "value cells");

        cells.forEach((cell) => {
            const text = cell.textContent.trim();
            const value = parseFloat(text);

            // Reset styles
            cell.style.backgroundColor = '';
            cell.style.color = '';
            cell.style.fontWeight = '';

            if (isNaN(value)) return;

            // Hide zeros
            if (value === 0) {
                cell.textContent = '';
                return;
            }

            // Value < 0 = Red
            if (value < 0) {
                cell.style.backgroundColor = '#ffe6e6';
                cell.style.color = '#cc0000';
                cell.style.fontWeight = 'bold';
            }
            // Value between 0 and 1 (inclusive) = Green
            // This catches 0.5, 1, and any value like 0.50, 1.00
            else if (value > 0 && value <= 1) {
                cell.style.backgroundColor = '#e6ffe6';
                cell.style.color = '#02ed02';
                cell.style.fontWeight = 'bold';
            }
            // Value > 1 = Red
            else if (value > 1) {
                cell.style.backgroundColor = '#ffe6e6';
                cell.style.color = '#cc0000';
                cell.style.fontWeight = 'bold';
            }
        });

        console.log("Pivot table processing complete");
    }
});