/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PivotRenderer } from "@web/views/pivot/pivot_renderer";
import { onMounted, onPatched } from "@odoo/owl";

patch(PivotRenderer.prototype, {
    setup() {
        super.setup();

        // Create style element for our custom CSS
        if (!document.getElementById('pivot_custom_styles')) {
            const style = document.createElement('style');
            style.id = 'pivot_custom_styles';
            document.head.appendChild(style);
        }

        onMounted(() => {
            setTimeout(() => this._processPivotTable(), 300);
            this._addMeasureListeners();
        });

        onPatched(() => {
            setTimeout(() => this._processPivotTable(), 300);
        });
    },

    _addMeasureListeners() {
        const pivotView = document.querySelector('.o_pivot');
        if (!pivotView) return;

        if (this._pivotClickHandler) {
            pivotView.removeEventListener('click', this._pivotClickHandler);
        }

        this._pivotClickHandler = (e) => {
            const isMeasureClick = e.target.closest('.o_pivot_buttons') ||
                                   e.target.closest('.dropdown-item') ||
                                   e.target.closest('button');

            if (isMeasureClick) {
                setTimeout(() => {
                    this._processPivotTable();
                }, 800);
            }
        };

        pivotView.addEventListener('click', this._pivotClickHandler);
    },

    _processPivotTable() {
        const table = document.querySelector('.o_pivot table');
        if (!table) return;

        const headerRows = table.querySelectorAll('thead tr');
        const lastHeaderRow = headerRows[headerRows.length - 1];
        const allHeaders = Array.from(lastHeaderRow.querySelectorAll('th'));



        const bodyRows = table.querySelectorAll('tbody tr');

        bodyRows.forEach((row, rowIdx) => {
            const allCells = Array.from(row.querySelectorAll('th, td'));
            const rowHeaderCount = allCells.filter(cell => cell.tagName.toLowerCase() === 'th').length;

            allCells.forEach((cell, cellIdx) => {
                if (!cell.classList.contains('o_pivot_cell_value')) {
                    return;
                }

                // Remove all our custom classes and reset styles
                cell.classList.remove('pivot-present-time', 'pivot-absent', 'pivot-late',
                                     'pivot-worked', 'pivot-days', 'pivot-negative',
                                     'pivot-absent-positive', 'pivot-absent-negative',
                                     'pivot-worked-good', 'pivot-worked-bad',
                                     'pivot-days-low', 'pivot-days-medium', 'pivot-days-good',
                                     'pivot-late-am', 'pivot-late-pm', 'pivot-leave-right',
                                     'pivot-leave-normal');
                cell.style.backgroundColor = '';
                cell.style.color = '';
                cell.style.fontWeight = '';
                cell.style.fontSize = '';
                cell.style.textAlign = '';
                cell.removeAttribute('data-time-value');

                const cleaned = cell.textContent.trim();
                const value = parseFloat(cleaned);

                if (isNaN(value)) return;

                const headerIdx = cellIdx - rowHeaderCount;
                if (headerIdx < 0 || headerIdx >= allHeaders.length) return;

                const fieldName = (allHeaders[headerIdx]?.textContent.trim() || "").toLowerCase();



                // RULE: Present / เข้างาน - store value and add class for CSS formatting
                if (fieldName.includes("present") || fieldName.includes("เข้างาน")) {
                    const hours = Math.floor(value);
                    const minutes = Math.round((value - hours) * 60);
                    const timeString = `${hours}:${minutes.toString().padStart(2, '0')}`;

                    // Store the time string in data attribute
                    cell.setAttribute('data-time-value', timeString);
                    cell.classList.add('pivot-present-time');

                    return;
                }

                // RULE: Absent / ขาด-มา
                if (fieldName.includes("absent") || fieldName.includes("deduction") || fieldName.includes("ขาด") || fieldName.includes("มา")) {

                    if (value > 0) {
                        cell.classList.add('pivot-absent-positive');
                    } else if (value < 0) {
                        cell.classList.add('pivot-absent-negative');
                    }
                    return;
                }

                // RULE: Late AM / ส.เช้า
                if ((fieldName.includes("late") && fieldName.includes("am")) ||
                    fieldName.includes("ส.เช้า") || fieldName.includes("สาย") && fieldName.includes("เช้า")) {

                    cell.classList.add('pivot-late-am');
                    return;
                }

                // RULE: Late PM / ส.บ่าย
                if ((fieldName.includes("late") && fieldName.includes("pm")) ||
                    fieldName.includes("ส.บ่าย") || fieldName.includes("สาย") && fieldName.includes("บ่าย")) {

                    cell.classList.add('pivot-late-pm');
                    return;
                }

                // RULE: Late (general) / สาย
                if (fieldName.includes("late") && fieldName.includes("min")) {

                    cell.classList.add('pivot-late-am');
                    return;
                }

                // RULE: Worked hours / วันทำงาน
                if (fieldName.includes("worked") || fieldName.includes("hour") || fieldName.includes("วันทำงาน")) {

                    if (value >= 8) {
                        cell.classList.add('pivot-worked-good');
                    } else if (value < 4) {
                        cell.classList.add('pivot-worked-bad');
                    }
                    return;
                }

                // RULE: Days / วัน
                if (fieldName.includes("days") || fieldName.includes("วัน")) {

                    if (value < 0.5) {
                        cell.classList.add('pivot-days-low');
                    } else if (value < 1) {
                        cell.classList.add('pivot-days-medium');
                    } else {
                        cell.classList.add('pivot-days-good');
                    }
                    return;
                }

                // RULE: Leave Rights / สิทธิหยุด
                if (fieldName.includes("leave") && fieldName.includes("right") || fieldName.includes("สิทธิหยุด")) {

                    cell.classList.add('pivot-leave-right');
                    return;
                }

                // RULE: Normal Leave / หยุดปกติ
                if (fieldName.includes("leave") && fieldName.includes("normal") || fieldName.includes("หยุดปกติ")) {

                    cell.classList.add('pivot-leave-normal');
                    return;
                }

                // DEFAULT: Negative
                if (value < 0) {

                    cell.classList.add('pivot-negative');
                }
            });
        });

        // Update CSS styles
        this._updateStyles();


    },

    _updateStyles() {
        const styleEl = document.getElementById('pivot_custom_styles');
        if (!styleEl) return;

        styleEl.textContent = `
            /* Present time / เข้างาน - hide original value, show formatted time */
            .pivot-present-time {
                font-weight: bold !important;
                font-size: 18px !important;
                color: #0066cc !important;
                text-align: center !important;
                position: relative !important;
            }

            .pivot-present-time::before {
                content: attr(data-time-value) !important;
                position: absolute !important;
                left: 0 !important;
                right: 0 !important;
                top: 0 !important;
                bottom: 0 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                background: white !important;
                color: #0066cc !important;
            }

            /* Absent / ขาด-มา - positive */
            .pivot-absent-positive {
                color: #16f224 !important;
                font-weight: bold !important;
                font-size: 16px !important;
            }

            /* Absent / ขาด-มา - negative */
            .pivot-absent-negative {
                color: #cc0000 !important;
                font-weight: bold !important;
                font-size: 20px !important;
            }

            /* Late AM / ส.เช้า */
            .pivot-late-am {
                color: #d104db !important;
                font-size: 16px !important;
                font-weight: bold !important;
            }

            /* Late PM / ส.บ่าย */
            .pivot-late-pm {
                color: #db8104 !important;
                font-size: 16px !important;
                font-weight: bold !important;
            }

            /* Worked hours / วันทำงาน - good */
            .pivot-worked-good {
                color: #0b800b !important;
                font-weight: bold !important;
            }

            /* Worked hours / วันทำงาน - bad */
            .pivot-worked-bad {
                color: #cc0000 !important;
                font-weight: bold !important;
            }

            /* Days / วัน - low */
            .pivot-days-low {
                color: #cc0000 !important;
                font-weight: bold !important;
            }

            /* Days / วัน - medium */
            .pivot-days-medium {
                color: #e6b800 !important;
                font-weight: bold !important;
            }

            /* Days / วัน - good */
            .pivot-days-good {
                color: #02ed02 !important;
                font-weight: bold !important;
            }

            /* Leave Rights / สิทธิหยุด */
            .pivot-leave-right {
                color: #9933ff !important;
                font-weight: bold !important;
            }

            /* Normal Leave / หยุดปกติ */
            .pivot-leave-normal {
                color: #0099cc !important;
                font-weight: bold !important;
            }

            /* Negative values */
            .pivot-negative {
                color: #cc0000 !important;
                font-weight: bold !important;
            }
        `;
    }
});