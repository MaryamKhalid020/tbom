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
    if (rows.length < 3) return; // Only apply if columns are grouped

    // For each intermediate grouping row, find the last th cell
    for (let i = 1; i < rows.length - 1; i++) {
        const tr = rows[i];
        const ths = tr.querySelectorAll('th');
        if (ths.length > 0) {
            const lastTh = ths[ths.length - 1];
            // If the cell is empty (contains no text or only whitespace), set it to "Total"
            if (lastTh && (lastTh.textContent.trim() === "" || lastTh.textContent.trim() === "Total")) {
                lastTh.textContent = "Total";
                lastTh.style.fontWeight = "bold";
                lastTh.style.textAlign = "center";
                lastTh.classList.add("tbom-pivot-total-header");
            }
        }
    }
}

// Start the observer when the DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startPivotObserver);
} else {
    startPivotObserver();
}
