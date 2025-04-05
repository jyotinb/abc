/** @odoo-module */

import { registry } from "@web/core/registry";
import { KpiCard } from "./kpi_card";
import { ChartRenderer } from "./chart_renderer";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

export class OwlSalesDashboard extends Component {
    setup() {
        this.state = useState({
            quotations: {
                value: 10,
                percentage: 6,
            },
            orders: {
                value: 0,
                percentage: 0,
                revenue: "$0.00K",
                revenue_percentage: 0,
                average: "$0.00K",
                average_percentage: 0,
            },
            topProducts: [],
            topSalesPeople: [],
            monthlySales: [],
            partnerOrders: [],
            period: 90,
        });
        this.orm = useService("orm");
        this.actionService = useService("action");

        onWillStart(async () => {
            this.getDates();
            await this.getQuotations();
            await this.getOrders();
            await this.getTopProducts();
            await this.getTopSalesPeople();
            await this.getMonthlySales();
            await this.getPartnerOrders();
        });
    }

    async onChangePeriod() {
        this.getDates();
        await this.getQuotations();
        await this.getOrders();
        await this.getTopProducts();
        await this.getTopSalesPeople();
        await this.getMonthlySales();
        await this.getPartnerOrders();
    }

    getDates() {
        // Using the luxon library that comes with Odoo instead of moment
        const DateTime = luxon.DateTime;
        const now = DateTime.now();
        this.state.current_date = now.minus({ days: this.state.period }).toFormat('yyyy-MM-dd');
        this.state.previous_date = now.minus({ days: this.state.period * 2 }).toFormat('yyyy-MM-dd');
    }

    async getQuotations() {
        let domain = [['state', 'in', ['sent', 'draft']]];
        if (this.state.period > 0){
            domain.push(['date_order', '>', this.state.current_date]);
        }
        const data = await this.orm.searchCount("sale.order", domain);
        this.state.quotations.value = data;

        let prev_domain = [['state', 'in', ['sent', 'draft']]];
        if (this.state.period > 0){
            prev_domain.push(['date_order','>', this.state.previous_date], ['date_order','<=', this.state.current_date]);
        }
        const prev_data = await this.orm.searchCount("sale.order", prev_domain);
        let percentage = 0;
        if (prev_data > 0) {
            percentage = ((data - prev_data)/prev_data) * 100;
        }
        this.state.quotations.percentage = percentage.toFixed(2);
    }

    async getOrders() {
        let domain = [['state', 'in', ['sale', 'done']]];
        if (this.state.period > 0){
            domain.push(['date_order','>', this.state.current_date]);
        }
        const data = await this.orm.searchCount("sale.order", domain);

        let prev_domain = [['state', 'in', ['sale', 'done']]];
        if (this.state.period > 0){
            prev_domain.push(['date_order','>', this.state.previous_date], ['date_order','<=', this.state.current_date]);
        }
        const prev_data = await this.orm.searchCount("sale.order", prev_domain);
        let percentage = 0;
        if (prev_data > 0) {
            percentage = ((data - prev_data)/prev_data) * 100;
        }

        const current_revenue = await this.orm.readGroup("sale.order", domain, ["amount_total:sum"], []);
        const prev_revenue = await this.orm.readGroup("sale.order", prev_domain, ["amount_total:sum"], []);
        let revenue_percentage = 0;
        if (prev_revenue[0].amount_total > 0) {
            revenue_percentage = ((current_revenue[0].amount_total - prev_revenue[0].amount_total) / prev_revenue[0].amount_total) * 100;
        }

        const current_average = await this.orm.readGroup("sale.order", domain, ["amount_total:avg"], []);
        const prev_average = await this.orm.readGroup("sale.order", prev_domain, ["amount_total:avg"], []);
        let average_percentage = 0;
        if (prev_average[0].amount_total > 0) {
            average_percentage = ((current_average[0].amount_total - prev_average[0].amount_total) / prev_average[0].amount_total) * 100;
        }

        this.state.orders = {
            value: data,
            percentage: percentage.toFixed(2),
            revenue: `$${(current_revenue[0].amount_total/1000).toFixed(2)}K`,
            revenue_percentage: revenue_percentage.toFixed(2),
            average: `$${(current_average[0].amount_total/1000).toFixed(2)}K`,
            average_percentage: average_percentage.toFixed(2),
        };
    }

    async getTopProducts() {
        let domain = [['state', 'in', ['sale', 'done']]];
        if (this.state.period > 0) {
            domain.push(['date_order', '>', this.state.current_date]);
        }
        const data = await this.orm.readGroup("sale.order.line", domain, ["product_id", "price_total:sum"], ["product_id"]);
        this.state.topProducts = data.map(item => ({ label: item.product_id[1], value: item.price_total }));
    }

    async getTopSalesPeople() {
        let domain = [['state', 'in', ['sale', 'done']]];
        if (this.state.period > 0) {
            domain.push(['date_order', '>', this.state.current_date]);
        }
        const data = await this.orm.readGroup("sale.order", domain, ["user_id", "amount_total:sum"], ["user_id"]);
        this.state.topSalesPeople = data.map(item => ({ label: item.user_id[1], value: item.amount_total }));
    }

    async getMonthlySales() {
        let domain = [['state', 'in', ['sale', 'done']]];
        if (this.state.period > 0) {
            domain.push(['date_order', '>', this.state.current_date]);
        }
        const data = await this.orm.readGroup("sale.order", domain, ["date_order:month", "amount_total:sum"], ["date_order:month"]);
        this.state.monthlySales = data.map(item => ({ label: item.date_order, value: item.amount_total }));
    }

    async getPartnerOrders() {
        let domain = [['state', 'in', ['sale', 'done']]];
        if (this.state.period > 0) {
            domain.push(['date_order', '>', this.state.current_date]);
        }
        const data = await this.orm.readGroup("sale.order", domain, ["partner_id", "amount_total:sum"], ["partner_id"]);
        this.state.partnerOrders = data.map(item => ({ label: item.partner_id[1], value: item.amount_total }));
    }

    async viewQuotations() {
        let domain = [['state', 'in', ['sent', 'draft']]];
        if (this.state.period > 0){
            domain.push(['date_order', '>', this.state.current_date]);
        }

        let list_view = await this.orm.searchRead("ir.model.data", [['name', '=', 'view_quotation_tree_with_onboarding']], ['res_id']);

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Quotations",
            res_model: "sale.order",
            domain,
            views: [
                [list_view.length > 0 ? list_view[0].res_id : false, "list"],
                [false, "form"],
            ]
        });
    }

    viewOrders() {
        let domain = [['state', 'in', ['sale', 'done']]];
        if (this.state.period > 0){
            domain.push(['date_order','>', this.state.current_date]);
        }

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Orders",
            res_model: "sale.order",
            domain,
            context: {group_by: ['date_order']},
            views: [
                [false, "list"],
                [false, "form"],
            ]
        });
    }

    viewRevenues() {
        let domain = [['state', 'in', ['sale', 'done']]];
        if (this.state.period > 0){
            domain.push(['date_order','>', this.state.current_date]);
        }

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Revenues",
            res_model: "sale.order",
            domain,
            context: {group_by: ['date_order']},
            views: [
                [false, "pivot"],
                [false, "form"],
            ]
        });
    }
}

OwlSalesDashboard.template = "owl.OwlSalesDashboard";
OwlSalesDashboard.components = { KpiCard, ChartRenderer };

registry.category("actions").add("owl.sales_dashboard", OwlSalesDashboard);
