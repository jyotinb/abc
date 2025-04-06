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
                value: 0,
                percentage: 0,
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
            current_date: null,
            previous_date: null,
            error: null,
            debugInfo: null,
            debug: {
                currentDate: null,
                previousDate: null,
                periodDays: 90
            }
        });
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.notification = useService("notification");

        onWillStart(async () => {
            try {
                this.getDates();
                await this.fetchDashboardData();
            } catch (error) {
                console.error('Dashboard Initialization Error:', error);
                this.state.error = error.message || 'Failed to load dashboard data';
                this.state.debugInfo = this.formatErrorForDisplay(error);
                this.notification.add(this.state.error, { 
                    type: 'danger',
                    sticky: true
                });
            }
        });
    }
	
	debugChartData() {
    console.log("Chart Data DEBUG:");
    console.log("Top Products:", this.state.topProducts);
    console.log("Top Products is Array?", Array.isArray(this.state.topProducts));
    
    console.log("Top Sales People:", this.state.topSalesPeople);
    console.log("Top Sales People is Array?", Array.isArray(this.state.topSalesPeople));
    
    console.log("Monthly Sales:", this.state.monthlySales);
    console.log("Monthly Sales is Array?", Array.isArray(this.state.monthlySales));
    
    console.log("Partner Orders:", this.state.partnerOrders);
    console.log("Partner Orders is Array?", Array.isArray(this.state.partnerOrders));
    
    // If you have access to the ChartRenderer code, add this debugging
    // to see what it's receiving:
    // In ChartRenderer component:
    // setup() {
    //     console.log("ChartRenderer props:", this.props);
    //     console.log("ChartRenderer data:", this.props.data);
    //     console.log("ChartRenderer data is Array?", Array.isArray(this.props.data));
    // }
}
	
	
	
    formatErrorForDisplay(error) {
        return {
            message: error.message,
            name: error.name,
            stack: error.stack,
            toString: () => JSON.stringify(error, Object.getOwnPropertyNames(error), 2)
        };
    }

    getDates() {
        const DateTime = luxon.DateTime;
        const now = DateTime.now();
        this.state.current_date = now.minus({ days: this.state.period }).toFormat('yyyy-MM-dd');
        this.state.previous_date = now.minus({ days: this.state.period * 2 }).toFormat('yyyy-MM-dd');
        
        // Update debug info
        this.state.debug = {
            currentDate: this.state.current_date,
            previousDate: this.state.previous_date,
            periodDays: this.state.period
        };
        
        console.log('Dashboard Date Range:', this.state.debug);
    }

    async fetchDashboardData() {
        console.log('Fetching Dashboard Data');
        console.log('Current Date:', this.state.current_date);
        console.log('Previous Date:', this.state.previous_date);

        try {
            await Promise.all([
                this.getQuotations(),
                this.getOrders(),
                this.getTopProducts(),
                this.getTopSalesPeople(),
                this.getMonthlySales(),
                this.getPartnerOrders()
            ]);
        } catch (error) {
            console.error('Detailed Fetch Error:', error);
            throw error;
        }
    }

    async onChangePeriod(days = 90) {
        try {
            // Update the period
            this.state.period = days;
            
            // Recalculate dates based on new period
            this.getDates();
            
            // Reset previous data
            this.state.quotations = {
                value: 0,
                percentage: 0,
            };
            this.state.orders = {
                value: 0,
                percentage: 0,
                revenue: "$0.00K",
                revenue_percentage: 0,
                average: "$0.00K",
                average_percentage: 0,
            };
            this.state.topProducts = [];
            this.state.topSalesPeople = [];
            this.state.monthlySales = [];
            this.state.partnerOrders = [];
            
            // Fetch new dashboard data
            await this.fetchDashboardData();
        } catch (error) {
            console.error('Period Change Error:', error);
            this.state.error = error.message || 'Failed to update dashboard data';
            this.state.debugInfo = this.formatErrorForDisplay(error);
            this.notification.add(this.state.error, { 
                type: 'danger',
                sticky: false
            });
        }
    }

    async getQuotations() {
        try {
            console.log('Fetching Quotations');
            
            // Current period domain
            let domain = [
                ['state', 'in', ['sent', 'draft']],
                ['create_date', '>', this.state.current_date]
            ];
            const data = await this.orm.searchCount("sale.order", domain);
            
            // Previous period domain
            let prev_domain = [
                ['state', 'in', ['sent', 'draft']],
                ['create_date', '>', this.state.previous_date],
                ['create_date', '<=', this.state.current_date]
            ];
            const prev_data = await this.orm.searchCount("sale.order", prev_domain);
            
            let percentage = prev_data > 0 
                ? ((data - prev_data) / prev_data) * 100 
                : 0;

            this.state.quotations = {
                value: data,
                percentage: percentage.toFixed(2)
            };
        } catch (error) {
            console.error('Quotations Fetch Error:', error);
            throw error;
        }
    }

    async getOrders() {
    try {
        console.log('Fetching Orders');
        
        // Current period domain
        let domain = [
            ['state', 'in', ['sale', 'done']],
            ['create_date', '>', this.state.current_date]
        ];
        const data = await this.orm.searchCount("sale.order", domain);

        // Previous period domain
        let prev_domain = [
            ['state', 'in', ['sale', 'done']],
            ['create_date', '>', this.state.previous_date],
            ['create_date', '<=', this.state.current_date]
        ];
        const prev_data = await this.orm.searchCount("sale.order", prev_domain);

        const current_revenue = await this.orm.readGroup("sale.order", domain, ["amount_total:sum"], []);
        const prev_revenue = await this.orm.readGroup("sale.order", prev_domain, ["amount_total:sum"], []);

        const current_average = await this.orm.readGroup("sale.order", domain, ["amount_total:avg"], []);
        const prev_average = await this.orm.readGroup("sale.order", prev_domain, ["amount_total:avg"], []);

        const calculatePercentage = (current, previous) => 
            previous > 0 ? ((current - previous) / previous) * 100 : 0;

        // Fix: Remove $ and K symbols, just display the numbers formatted
        const currentRevenueValue = current_revenue[0]?.amount_total || 0;
        const prevRevenueValue = prev_revenue[0]?.amount_total || 0;
        const currentAverageValue = current_average[0]?.amount_total || 0;
        const prevAverageValue = prev_average[0]?.amount_total || 0;

        this.state.orders = {
            value: data,
            percentage: calculatePercentage(data, prev_data).toFixed(2),
            revenue: currentRevenueValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}),
            revenue_percentage: calculatePercentage(
                currentRevenueValue, 
                prevRevenueValue
            ).toFixed(2),
            average: currentAverageValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}),
            average_percentage: calculatePercentage(
                currentAverageValue, 
                prevAverageValue
            ).toFixed(2)
        };
    } catch (error) {
        console.error('Orders Fetch Error:', error);
        throw error;
    }
}

    async getTopProducts() {
    try {
        console.log('Fetching Top Products');
        
        let domain = [
            ['state', 'in', ['sale', 'done']],
            ['order_id.create_date', '>', this.state.current_date]
        ];
        
        // Fixed: Changed groupby parameter to an array instead of object
        const data = await this.orm.readGroup("sale.order.line", domain, 
            ["product_id", "price_total:sum"], 
            ["product_id"]
        );
        console.log('Top Products:', data);
        
        this.state.topProducts = data
            .filter(item => item.product_id) // Ensure product exists
            .map(item => ({ 
                label: item.product_id[1] || 'Unknown', 
                value: item.price_total || 0 
            }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 10);
    } catch (error) {
        console.error('Top Products Fetch Error:', error);
        throw error;
    }
}

    async getTopSalesPeople() {
    try {
        console.log('Fetching Top Sales People');
        
        let domain = [
            ['state', 'in', ['sale', 'done']],
            ['create_date', '>', this.state.current_date]
        ];
        
        // Fixed: Changed groupby parameter to an array instead of object
        const data = await this.orm.readGroup("sale.order", domain, 
            ["user_id", "amount_total:sum"], 
            ["user_id"]
        );
        console.log('Top Sales People:', data);
        
        this.state.topSalesPeople = data
            .filter(item => item.user_id) // Ensure user exists
            .map(item => ({ 
                label: item.user_id[1] || 'Unknown', 
                value: item.amount_total || 0 
            }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 10);
    } catch (error) {
        console.error('Top Sales People Fetch Error:', error);
        throw error;
    }
}

    // Fix for getMonthlySales to properly display month names
async getMonthlySales() {
    try {
        console.log('Fetching Monthly Sales');
        
        let domain = [
            ['state', 'in', ['sale', 'done']],
            ['create_date', '>', this.state.current_date]
        ];
        
        // Use the correct groupby format for Odoo
        const data = await this.orm.readGroup("sale.order", domain, 
            ["amount_total:sum"], 
            ["create_date:month"]
        );
        
        // Debug the actual response to see what fields are returned
        console.log('Raw Monthly Sales Data:', JSON.stringify(data));
        
        const formattedData = [];
        
        for (const item of data) {
            // Try all possible field name combinations based on how Odoo might return the data
            // Odoo sometimes uses different field naming conventions based on version
            let monthLabel = 'Unknown';
            
            // Loop through all properties to find the one containing month info
            for (const key in item) {
                // Look for field names that could contain month data
                if (key === 'create_date_month' || 
                    key === 'create_date:month' || 
                    key === 'create_date' || 
                    key.includes('month') || 
                    key.includes('date')) {
                    
                    if (item[key] && typeof item[key] === 'string') {
                        monthLabel = item[key];
                        console.log(`Found month label in field "${key}": ${monthLabel}`);
                        break;
                    }
                }
            }
            
            formattedData.push({
                label: monthLabel,
                value: Number(item.amount_total || 0)
            });
        }
        
        // Sort by date (assuming format is "Month Year" or similar)
        formattedData.sort((a, b) => a.label.localeCompare(b.label));
        this.state.monthlySales = formattedData.slice(0, 12);
        
        console.log('Formatted Monthly Sales Data:', this.state.monthlySales);
    } catch (error) {
        console.error('Monthly Sales Fetch Error:', error);
        throw error;
    }
}

    async getPartnerOrders() {
    try {
        console.log('Fetching Partner Orders');
        
        let domain = [
            ['state', 'in', ['sale', 'done']],
            ['create_date', '>', this.state.current_date]
        ];
        
        // Fixed: Changed groupby parameter to an array instead of object
        const data = await this.orm.readGroup("sale.order", domain, 
            ["partner_id", "amount_total:sum"], 
            ["partner_id"]
        );
        console.log('Partner Orders:', data);
        
        this.state.partnerOrders = data
            .filter(item => item.partner_id) // Ensure partner exists
            .map(item => ({ 
                label: item.partner_id[1] || 'Unknown', 
                value: item.amount_total || 0 
            }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 10);
    } catch (error) {
        console.error('Partner Orders Fetch Error:', error);
        throw error;
    }
}

    async viewQuotations() {
        let domain = [['state', 'in', ['sent', 'draft']]];

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

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Orders",
            res_model: "sale.order",
            domain,
            context: {group_by: ['create_date']},
            views: [
                [false, "list"],
                [false, "form"],
            ]
        });
    }

    viewRevenues() {
        let domain = [['state', 'in', ['sale', 'done']]];

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Revenues",
            res_model: "sale.order",
            domain,
            context: {group_by: ['create_date']},
            views: [
                [false, "pivot"],
                [false, "form"],
            ]
        });
    }
	
	async fetchDashboardData() {
    console.log('Fetching Dashboard Data');
    console.log('Current Date:', this.state.current_date);
    console.log('Previous Date:', this.state.previous_date);

    try {
        await Promise.all([
            this.getQuotations(),
            this.getOrders(),
            this.getTopProducts(),
            this.getTopSalesPeople(),
            this.getMonthlySales(),
            this.getPartnerOrders()
        ]);
        
        // Add this line to debug chart data after fetching
        this.debugChartData();
    } catch (error) {
        console.error('Detailed Fetch Error:', error);
        throw error;
    }
}
	
	
}

OwlSalesDashboard.template = "owl.OwlSalesDashboard";
OwlSalesDashboard.components = { KpiCard, ChartRenderer };

registry.category("actions").add("owl.sales_dashboard", OwlSalesDashboard);