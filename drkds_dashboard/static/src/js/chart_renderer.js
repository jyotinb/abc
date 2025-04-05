/** @odoo-module */

import { useState, onWillUpdateProps } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";

export class ChartRenderer extends Component {
    setup() {
        this.state = useState({ chart: null });
        onWillUpdateProps(() => {
            if (this.state.chart) {
                this.updateChart();
            }
        });
    }

    mounted() {
        this.renderChart();
    }

    renderChart() {
        const ctx = this.el.querySelector('canvas').getContext('2d');
        this.state.chart = new Chart(ctx, {
            type: this.props.type,
            data: {
                labels: this.props.data.map(item => item.label),
                datasets: [{
                    label: this.props.label,
                    data: this.props.data.map(item => item.value),
                    backgroundColor: this.props.backgroundColor || 'rgba(75, 192, 192, 0.2)',
                    borderColor: this.props.borderColor || 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: this.props.options || {}
        });
    }

    updateChart() {
        this.state.chart.data.labels = this.props.data.map(item => item.label);
        this.state.chart.data.datasets[0].data = this.props.data.map(item => item.value);
        this.state.chart.update();
    }
}

ChartRenderer.template = "owl.ChartRenderer";
