/** @odoo-module **/

import { registry } from "@web/core/registry";
import { X2ManyField } from "@web/views/fields/x2many/x2many_field";
import { useService } from "@web/core/utils/hooks";

/**
 * Custom widget for section-specific one2many fields
 * Provides better filtering and display for greenhouse sections
 */
export class SectionOne2ManyField extends X2ManyField {
    setup() {
        super.setup();
        this.orm = useService("orm");
    }

    /**
     * Override to add section-specific context
     */
    get context() {
        const context = super.context;
        // Add section-specific context from domain
        if (this.props.domain) {
            const sectionDomain = this.props.domain.find(
                d => Array.isArray(d) && d[0] === 'section_id'
            );
            if (sectionDomain && sectionDomain[2]) {
                context.default_section_id = sectionDomain[2];
            }
        }
        return context;
    }

    /**
     * Custom display for section fields
     */
    get displayName() {
        const sectionId = this.context.default_section_id;
        if (sectionId) {
            return `Section ${sectionId} Inputs`;
        }
        return super.displayName;
    }
}

// Register the widget
registry.category("fields").add("section_one2many", SectionOne2ManyField);