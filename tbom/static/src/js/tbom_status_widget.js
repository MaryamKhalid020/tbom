/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

export class TbomStatusEditWidget extends Component {
    setup() {
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        this.state = useState({
            isOpen: false,
        });
    }

    get currentStatusValue() {
        return this.props.record.data[this.props.name];
    }

    get currentStatusLabel() {
        const val = this.currentStatusValue;
        const option = this.options.find(opt => opt[0] === val);
        return option ? option[1] : val;
    }

    get options() {
        return this.props.record.fields[this.props.name].selection || [];
    }

    get badgeClass() {
        const val = this.currentStatusValue;
        switch (val) {
            case 'planned': return 'text-bg-info text-white';
            case 'deployed': return 'text-bg-warning text-dark';
            case 'returned': return 'text-bg-success text-white';
            case 'damaged': return 'text-bg-danger text-white';
            case 'setup': return 'text-bg-primary text-white';
            case 'active': return 'text-bg-success text-white';
            case 'closing': return 'text-bg-warning text-dark';
            case 'closed': return 'text-bg-secondary text-white';
            case 'cancelled': return 'text-bg-dark text-white';
            default: return 'btn-light';
        }
    }

    toggleDropdown(ev) {
        ev.stopPropagation();
        if (this.props.readonly) {
            return;
        }
        this.state.isOpen = !this.state.isOpen;
    }

    closeDropdown() {
        this.state.isOpen = false;
    }

    async selectStatus(option, ev) {
        ev.stopPropagation();
        this.closeDropdown();
        
        const newValue = option[0];
        const newLabel = option[1];
        const oldValue = this.currentStatusValue;
        const oldLabel = this.currentStatusLabel;

        if (newValue === oldValue) {
            return;
        }

        const recordName = this.props.record.data.display_name || this.props.record.data.name || "Record";
        const modelName = this.props.record.resModel;
        
        let entityName = "Record";
        if (modelName === "tbom.equipment") entityName = "Equipment";
        else if (modelName === "tbom.resource") entityName = "Resource";
        else if (modelName === "tbom.temporary.operation") entityName = "Temporary Operation";

        const title = _t("Update {} Status?").replace("{}", entityName);
        const body = _t("Are you sure you want to change the {} status from \"{}\" to \"{}\"?")
            .replace("{}", entityName)
            .replace("{}", oldLabel)
            .replace("{}", newLabel);

        this.dialog.add(ConfirmationDialog, {
            title: title,
            body: body,
            confirmLabel: _t("Confirm / Update"),
            cancelLabel: _t("Cancel"),
            confirm: async () => {
                try {
                    if (this.props.record.resId) {
                        await this.props.record.model.orm.write(
                            this.props.record.resModel,
                            [this.props.record.resId],
                            { [this.props.name]: newValue }
                        );
                        await this.props.record.load();
                    } else {
                        await this.props.record.update({ [this.props.name]: newValue });
                    }
                    this.notification.add(_t("{} status updated successfully.").replace("{}", entityName), {
                        type: "success",
                    });
                } catch (error) {
                    console.error("Failed to update status", error);
                }
            },
            cancel: () => {},
        });
    }
}

TbomStatusEditWidget.template = "tbom.TbomStatusEditWidget";
TbomStatusEditWidget.props = {
    ...standardFieldProps,
};

registry.category("fields").add("tbom_status_edit", {
    component: TbomStatusEditWidget,
    supportedTypes: ["selection"],
});
