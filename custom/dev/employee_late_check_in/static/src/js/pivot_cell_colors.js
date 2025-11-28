/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PivotRenderer } from "@web/views/pivot/pivot_renderer";
import { onMounted, onPatched } from "@odoo/owl";

patch(PivotRenderer.prototype, {
    setup() {
        super.setup();
        const processTable = () => {
            setTimeout(() => {
                requestAnimationFrame(() => this._processPivotTable());
            }, 50);
        };

        onMounted(processTable);
        onPatched(processTable);
    },

    _processPivotTable() {
        const table = document.querySelector('.o_pivot table');
        if (!table) return;

        // Get the LAST header row
        const headerRows = table.querySelectorAll('thead tr');
        const lastHeaderRow = headerRows[headerRows.length - 1];
        const allHeaders = Array.from(lastHeaderRow.querySelectorAll('th'));

        const bodyRows = table.querySelectorAll('tbody tr');

        bodyRows.forEach((row) => {
            const allCells = Array.from(row.querySelectorAll('th, td'));

            // Count how many <th> cells (row headers) are in this row
            const rowHeaderCount = allCells.filter(cell => cell.tagName.toLowerCase() === 'th').length;

            console.log(`Row has ${rowHeaderCount} row header(s)`);

            allCells.forEach((cell, cellIdx) => {
                // Only process value cells
                if (!cell.classList.contains('o_pivot_cell_value')) {
                    return;
                }

                const cleaned = cell.textContent.trim();
                const value = parseFloat(cleaned);

                // Reset styles
                cell.style.backgroundColor = '';
                cell.style.color = '';
                cell.style.fontWeight = '';
                cell.style.fontSize = '';

                if (isNaN(value)) return;
                if (value === 0) {
                    cell.textContent = '';
                    return;
                }

                // IMPORTANT: Adjust header index by subtracting row header count
                // If cellIdx = 2 and rowHeaderCount = 1, then headerIdx = 2 - 1 = 1
                const headerIdx = cellIdx - rowHeaderCount;
                const fieldName = (allHeaders[headerIdx]?.textContent.trim() || "").toLowerCase();

                console.log(`Cell[${cellIdx}] -> Header[${headerIdx}]: "${fieldName}" = ${value}`);

                // RULE: check-in time (convert float to H:MM - no leading zero)
                if (fieldName.includes("check-in time") || fieldName.includes("present")) {
                    console.log(`  -> CHECK-IN TIME: ${value}`);

                    // Convert float to H:MM format (no leading zero for hour)
                    const hours = Math.floor(value);
                    const minutes = Math.round((value - hours) * 60);
                    const timeString = `${hours}:${minutes.toString().padStart(2, '0')}`;

                    cell.textContent = timeString;
                    cell.style.fontWeight = 'bold';
                    cell.style.fontSize = '14px';
                    cell.style.color = '#0066cc';
                    cell.style.textAlign = 'center';  // Center the text
                    return;
                }

                // RULE: absent deduction
                if (fieldName.includes("absent") || fieldName.includes("deduction")) {
                    console.log("  -> ABSENT");
                    if (value > 0) {
                        cell.style.color = '#16f224';
                        cell.style.fontWeight = 'bold';
                        cell.style.fontSize = '16px';
                    }
                    else if (value < 0) {
                        cell.style.color = '#cc0000';
                        cell.style.fontWeight = 'bold';
                        cell.style.fontSize = '16px';
                    }
                    return;
                }

                // RULE: late columns (add warning symbol)
                if (fieldName.includes("late") && fieldName.includes("min")) {
                    console.log("  -> LATE");
                    const absValue = Math.abs(value);
                    cell.style.color = '#05a1f5';
                    cell.style.fontWeight = 'bold';
                    return;
                }

                // RULE: worked hours
                if (fieldName.includes("worked") || fieldName.includes("hour")) {
                    console.log("  -> WORKED HOURS");
                    if (value >= 8) {
                        cell.style.color = '#0b800b';
                        cell.style.fontWeight = 'bold';
                    } else if (value < 4) {
                        cell.style.color = '#cc0000';
                        cell.style.fontWeight = 'bold';
                    }
                    return;
                }

                // RULE: days work
                if (fieldName.includes("days")) {
                    console.log("  -> DAYS WORK");
                    if (value < 0.5) {
                        cell.style.color = '#cc0000';
                        cell.style.fontWeight = 'bold';
                    } else if (value < 1) {
                        cell.style.color = '#e6b800';
                        cell.style.fontWeight = 'bold';
                    } else {
                        cell.style.color = '#02ed02';
                        cell.style.fontWeight = 'bold';
                    }
                    return;
                }

                // DEFAULT: negative values
                if (value < 0) {
                    cell.style.color = '#cc0000';
                    cell.style.fontWeight = 'bold';
                }
            });
        });
    }
});