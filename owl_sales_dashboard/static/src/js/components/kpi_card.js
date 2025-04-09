/** @odoo-module */

import { Component } from "@odoo/owl";

export class KpiCard extends Component {
    static template = "owl.KpiCard";
    static props = {
        title: { type: String, optional: true },
        value: { type: [Number, String], optional: true },
        percentage: { type: [Number, String], optional: true },
        onClick: { type: Function, optional: true }
    };

    get isPositive() {
        return parseFloat(this.props.percentage) >= 0;
    }

    get formattedPercentage() {
        const percentage = parseFloat(this.props.percentage);
        return (percentage >= 0 ? "+" : "") + percentage + "%";
    }

    onCardClick() {
        if (this.props.onClick) {
            this.props.onClick();
        }
    }
}