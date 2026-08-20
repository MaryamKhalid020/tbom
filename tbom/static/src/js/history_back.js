/** @odoo-module **/
import { registry } from '@web/core/registry';

async function goBack(env, action) {
    env.services.action.restore();
}

registry.category('actions').add('history_back', goBack);
