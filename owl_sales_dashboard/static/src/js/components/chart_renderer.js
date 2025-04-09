/** @odoo-module */

import { Component } from "@odoo/owl";

export class ChartRenderer extends Component {
    static template = "owl.ChartRenderer";
    static props = {
        type: { type: String, optional: true },
        data: { type: Array, optional: true },
        label: { type: String, optional: true },
        backgroundColor: { type: String, optional: true },
        borderColor: { type: String, optional: true },
        options: { type: Object, optional: true }
    };

    setup() {
        // Ensure Chart.js is loaded
        if (typeof Chart === 'undefined') {
            console.error('Chart.js is not loaded');
            return;
        }
    }

    mounted() {
        this.renderChart();
    }

    renderChart() {
        const canvas = this.el.querySelector('canvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        // Destroy existing chart if any
        if (this.chart) {
            this.chart.destroy();
        }

        // Provide default data if no data is available
        const chartData = this.props.data && this.props.data.length > 0 
            ? this.props.data 
            : [{ label: 'No Data', value: 0 }];

        // Create new chart
        this.chart = new Chart(ctx, {
            type: this.props.type || 'bar',
            data: {
                labels: chartData.map(item => item.label),
                datasets: [{
                    label: this.props.label || 'Data',
                    data: chartData.map(item => item.value),
                    backgroundColor: this.props.backgroundColor || 'rgba(75, 192, 192, 0.2)',
                    borderColor: this.props.borderColor || 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                ...(this.props.options || {}),
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    willUnmount() {
        // Cleanup chart when component is destroyed
        if (this.chart) {
            this.chart.destroy();
        }
    }
}