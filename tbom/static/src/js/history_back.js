/** @odoo-module **/
import { registry } from '@web/core/registry';

async function goBack(env, action) {
    env.services.action.restore();
}

registry.category('actions').add('history_back', goBack);

// MutationObserver to automatically fix Odoo pivot table empty column headers
let observer = null;

function startPivotObserver() {
    if (observer) return;
    
    observer = new MutationObserver((mutations) => {
        const pivotView = document.querySelector('.o_pivot_view');
        if (pivotView) {
            fixPivotHeaders();
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

function fixPivotHeaders() {
    const table = document.querySelector('.o_pivot_view table');
    if (!table) return;
    const rows = table.querySelectorAll('thead tr');
    if (rows.length < 3) return; // Only apply if columns are grouped (at least 3 rows in thead)

    // Get the measures row (last row) to determine total columns
    const lastRow = rows[rows.length - 1];
    const lastRowThs = Array.from(lastRow.querySelectorAll('th'));
    const totalCols = lastRowThs.length;

    // For each intermediate grouping row
    for (let i = 1; i < rows.length - 1; i++) {
        const tr = rows[i];
        if (tr.querySelector('.tbom-pivot-total-header')) {
            continue; // Already added
        }

        // Calculate the sum of colspans of the existing cells in this row
        const ths = Array.from(tr.querySelectorAll('th'));
        let sumColspan = 0;
        ths.forEach(th => {
            const colspan = parseInt(th.getAttribute('colspan') || '1', 10);
            sumColspan += colspan;
        });

        // The difference is the missing columns for the Grand Total!
        const missingColspan = totalCols - sumColspan;
        if (missingColspan > 0) {
            // Create the missing "Total" header cell
            const totalTh = document.createElement('th');
            totalTh.className = 'tbom-pivot-total-header o_pivot_header_cell_closed text-center font-weight-bold';
            totalTh.style.fontWeight = 'bold';
            totalTh.style.textAlign = 'center';
            totalTh.setAttribute('colspan', missingColspan.toString());
            totalTh.textContent = 'Total';
            
            // Append it to the row
            tr.appendChild(totalTh);
        }
    }
}

// Start the observer when the DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startPivotObserver);
} else {
    startPivotObserver();
}
