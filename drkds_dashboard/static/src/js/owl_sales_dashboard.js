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
