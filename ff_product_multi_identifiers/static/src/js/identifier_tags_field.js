import { Component, proxy, signal, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class IdentifierTagsField extends Component {
    static template = "ff_product_multi_identifiers.IdentifierTagsField";
    props = useProps(standardFieldProps);

    setup() {
        this.state = proxy({ value: "" });
        this.inputRef = signal.ref();
    }

    get adapterField() {
        return this.props.adapterField ||
            (this.props.name === "default_code"
                ? "ff_internal_identifier_data"
                : "ff_barcode_identifier_data");
    }

    get primaryValue() {
        return this.props.record.data[this.props.name] || "";
    }

    get aliases() {
        return this.props.record.data[this.adapterField] || [];
    }

    get tags() {
        const tags = [];
        if (this.primaryValue) {
            tags.push({
                id: "primary",
                props: {
                    text: this.primaryValue,
                    tooltip: "Primary identifier",
                    onDelete: this.props.readonly ? undefined : () => this.removePrimary(),
                },
            });
        }
        for (const alias of this.aliases) {
            tags.push({
                id: alias.id || `new-${alias.name}`,
                props: {
                    text: alias.name,
                    tooltip: "Alternative identifier",
                    onDelete: this.props.readonly ? undefined : () => this.removeAlias(alias),
                },
            });
        }
        return tags;
    }

    onInput(ev) {
        this.state.value = ev.target.value;
    }

    async onKeydown(ev) {
        if (ev.key === "Escape") {
            ev.preventDefault();
            this.state.value = "";
            return;
        }
        if (ev.key === "Backspace" && !this.state.value && this.aliases.length) {
            ev.preventDefault();
            await this.removeAlias(this.aliases[this.aliases.length - 1]);
            return;
        }
        if (ev.key !== "Enter") {
            return;
        }
        ev.preventDefault();
        ev.stopPropagation();
        await this.addIdentifier();
    }

    async addIdentifier() {
        const value = this.state.value.trim();
        if (!value || this.props.readonly) {
            return;
        }
        if (value === this.primaryValue || this.aliases.some((alias) => alias.name === value)) {
            this.state.value = "";
            return;
        }
        if (!this.primaryValue) {
            await this.props.record.update({ [this.props.name]: value });
        } else {
            await this.props.record.update({
                [this.adapterField]: [
                    ...this.aliases,
                    { id: `new-${Date.now()}`, name: value, sequence: (this.aliases.length + 1) * 10 },
                ],
            });
        }
        this.state.value = "";
        this.inputRef.el?.focus();
    }

    async removePrimary() {
        const aliases = [...this.aliases];
        if (aliases.length) {
            const [next, ...remaining] = aliases;
            await this.props.record.update({
                [this.props.name]: next.name,
                [this.adapterField]: remaining,
            });
        } else {
            await this.props.record.update({ [this.props.name]: false });
        }
    }

    async removeAlias(alias) {
        await this.props.record.update({
            [this.adapterField]: this.aliases.filter((candidate) => candidate !== alias),
        });
    }
}

registry.category("fields").add("ff_identifier_tags", {
    component: IdentifierTagsField,
    supportedTypes: ["char"],
    extractProps: ({ options }) => ({
        adapterField: options.adapter_field,
    }),
});
