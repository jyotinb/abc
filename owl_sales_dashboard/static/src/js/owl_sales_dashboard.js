/** @odoo-module */

import { registry } from "@web/core/registry";
import { KpiCard } from "./components/kpi_card";
import { ChartRenderer } from "./components/chart_renderer";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

export class OwlSalesDashboard extends Component {
    setup() {
        this.state = useState({
            // KPI data
            quotations: { value: 0, percentage: 0 },
            orders: {
                value: 0,
                percentage: 0,
                revenue: 0,
                revenue_percentage: 0,
                average: 0,
                average_percentage: 0,
            },
            topProducts: [],
            topSalesPeople: [],
            monthlySales: [],
            partnerOrders: [],
            
            // Filters
            period: 90,
            customDateRange: false,
            startDate: null,
            endDate: null,
            
            // New filters
            selectedCategories: [],
            selectedTeams: [],
            
            // Data for filters
            productCategories: [],
            salesTeams: [],
            
            // UI states
            loading: true,
            error: null,
            showFilters: false
        });
        
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.notification = useService("notification");
        
        // Cache for category filtered order IDs
        this.categoryFilteredOrderIds = null;

        onWillStart(async () => {
            try {
                // Set default dates
                this.setDefaultDates();
                
                // Load filter data
                await this.loadFilterData();
                
                // Fetch dashboard data
                await this.fetchDashboardData();
            } catch (error) {
                console.error('Dashboard Initialization Error:', error);
                this.state.error = error.message || 'Failed to load dashboard data';
                this.notification.add(this.state.error, { 
                    type: 'danger',
                    sticky: true
                });
            } finally {
                this.state.loading = false;
            }
        });
    }
    
    setDefaultDates() {
        const now = luxon.DateTime.now();
        const startDate = now.minus({ days: this.state.period });
        
        this.state.startDate = startDate.toFormat('yyyy-MM-dd');
        this.state.endDate = now.toFormat('yyyy-MM-dd');
    }

    async loadFilterData() {
        try {
            // Load ALL product categories without filtering
            const categories = await this.orm.searchRead(
                'product.category',
                [], // No domain filter - get all categories
                ['id', 'name', 'display_name', 'parent_id']
            );
            
            console.log('Available product categories:', categories);
            this.state.productCategories = categories;
            
            // Load sales teams
            const teams = await this.orm.searchRead(
                'crm.team',
                [],
                ['id', 'name']
            );
            console.log('Available sales teams:', teams);
            this.state.salesTeams = teams;
        } catch (error) {
            console.error('Error loading filter data:', error);
            this.notification.add('Error loading filter data: ' + error.message, { 
                type: 'danger',
                sticky: false
            });
            // Don't throw, just continue with empty filters
            this.state.productCategories = [];
            this.state.salesTeams = [];
        }
    }
    
    getDates() {
        if (this.state.customDateRange) {
            return {
                current_date: this.state.startDate,
                previous_date: luxon.DateTime
                    .fromFormat(this.state.startDate, 'yyyy-MM-dd')
                    .minus({ days: luxon.DateTime
                        .fromFormat(this.state.endDate, 'yyyy-MM-dd')
                        .diff(luxon.DateTime.fromFormat(this.state.startDate, 'yyyy-MM-dd'), 'days')
                        .days
                    })
                    .toFormat('yyyy-MM-dd')
            };
        }
        
        const now = luxon.DateTime.now();
        return {
            current_date: now.minus({ days: this.state.period }).toFormat('yyyy-MM-dd'),
            previous_date: now.minus({ days: this.state.period * 2 }).toFormat('yyyy-MM-dd')
        };
    }

    buildDomainFilters() {
        let domain = [];
        
        // Add sales team filter
        if (this.state.selectedTeams.length > 0) {
            domain.push(['team_id', 'in', this.state.selectedTeams]);
        }
        
        return domain;
    }
    
    // Updated getCategoryFilteredOrderIds method with better debugging
    async getCategoryFilteredOrderIds() {
        // Skip if no categories selected
        if (!this.state.selectedCategories.length) {
            console.log('No categories selected, skipping filter');
            return null; // null means "no filtering needed"
        }
        
        console.log('Filtering by categories:', this.state.selectedCategories);
        
        // If we've already calculated this, return the cached result
        if (this.categoryFilteredOrderIds !== null) {
            console.log('Using cached category order IDs');
            return this.categoryFilteredOrderIds;
        }
        
        try {
            // First, verify that the categories exist
            const categories = await this.orm.searchRead(
                'product.category',
                [['id', 'in', this.state.selectedCategories]],
                ['id', 'name']
            );
            
            console.log('Found matching categories:', categories);
            
            if (!categories.length) {
                console.error('No matching categories found in database!');
                this.notification.add('Selected category IDs not found in the database', { 
                    type: 'warning',
                    sticky: false
                });
                // Return empty array - no matches will be found
                this.categoryFilteredOrderIds = [];
                return [];
            }
            
            // Simple search for order lines with products in these categories
            console.log('Looking for order lines with products in categories:', this.state.selectedCategories);
            const orderLines = await this.orm.searchRead(
                'sale.order.line',
                [['product_id.categ_id', 'in', this.state.selectedCategories]],
                ['order_id', 'product_id', 'name']
            );
            
            console.log('Found matching order lines:', orderLines);
            
            // Extract unique order IDs - handle both array and object formats
            const orderIds = [...new Set(orderLines.map(line => 
                Array.isArray(line.order_id) ? line.order_id[0] : line.order_id
            ))];
            
            console.log('Extracted order IDs:', orderIds);
            
            // Cache the result
            this.categoryFilteredOrderIds = orderIds.length ? orderIds : [];
            return this.categoryFilteredOrderIds;
        } catch (error) {
            console.error('Error getting filtered order IDs:', error);
            this.notification.add('Error applying category filter: ' + error.message, { 
                type: 'danger',
                sticky: false
            });
            return null; // On error, skip filtering
        }
    }

    async fetchDashboardData() {
        const { current_date, previous_date } = this.getDates();
        const additionalFilters = this.buildDomainFilters();
        
        // Reset category filter cache when fetching new data
        this.categoryFilteredOrderIds = null;
        
        // Reset error state
        this.state.error = null;
        
        // Execute these one by one with error handling for each
        try {
            // Get quotations data
            try {
                await this.getQuotations(current_date, previous_date, additionalFilters);
            } catch (error) {
                console.error('Quotations Fetch Error:', error);
                this.state.error = (this.state.error || "") + "Error loading quotations data. ";
            }
            
            // Get orders data
            try {
                await this.getOrders(current_date, previous_date, additionalFilters);
            } catch (error) {
                console.error('Orders Fetch Error:', error);
                this.state.error = (this.state.error || "") + "Error loading orders data. ";
            }
            
            // Get top products
            try {
                await this.getTopProducts(current_date, additionalFilters);
            } catch (error) {
                console.error('Top Products Fetch Error:', error);
                this.state.error = (this.state.error || "") + "Error loading top products data. ";
            }
            
            // Get top sales people
            try {
                await this.getTopSalesPeople(current_date, additionalFilters);
            } catch (error) {
                console.error('Top Sales People Fetch Error:', error);
                this.state.error = (this.state.error || "") + "Error loading top sales people data. ";
            }
            
            // Get monthly sales
            try {
                await this.getMonthlySales(current_date, additionalFilters);
            } catch (error) {
                console.error('Monthly Sales Fetch Error:', error);
                this.state.error = (this.state.error || "") + "Error loading monthly sales data. ";
            }
            
            // Get partner orders
            try {
                await this.getPartnerOrders(current_date, additionalFilters);
            } catch (error) {
                console.error('Partner Orders Fetch Error:', error);
                this.state.error = (this.state.error || "") + "Error loading partner orders data. ";
            }
        } catch (error) {
            console.error('Detailed Fetch Error:', error);
            this.state.error = (this.state.error || "") + "General dashboard loading error. ";
        }
    }

    // Period change handler
    async onChangePeriod(days) {
        try {
            this.state.loading = true;
            this.state.period = days;
            this.state.customDateRange = false;
            this.setDefaultDates();
            await this.fetchDashboardData();
        } catch (error) {
            console.error('Period Change Error:', error);
            this.state.error = error.message || 'Failed to update dashboard data';
            this.notification.add(this.state.error, { 
                type: 'danger',
                sticky: false
            });
        } finally {
            this.state.loading = false;
        }
    }
    
    // Custom date range handler
    async onDateRangeChange() {
        try {
            this.state.loading = true;
            this.state.customDateRange = true;
            await this.fetchDashboardData();
        } catch (error) {
            console.error('Date Range Change Error:', error);
            this.state.error = error.message || 'Failed to update dashboard data';
            this.notification.add(this.state.error, { 
                type: 'danger',
                sticky: false
            });
        } finally {
            this.state.loading = false;
        }
    }
    
    // Category filter change handler with better debugging
    async onCategoryChange(event) {
        try {
            const selectedOptions = Array.from(event.target.selectedOptions).map(option => {
                // Parse to integer
                const id = parseInt(option.value);
                console.log(`Selected category: ID=${id}, Label=${option.text}`);
                return id;
            });
            
            console.log('All selected categories:', selectedOptions);
            
            // Set the state
            this.state.selectedCategories = selectedOptions;
            
            // Reset category filter cache when categories change
            this.categoryFilteredOrderIds = null;
            
            // Apply the filters
            await this.applyFilters();
        } catch (error) {
            console.error('Error in category change handler:', error);
            this.notification.add('Error changing categories: ' + error.message, { 
                type: 'danger',
                sticky: false
            });
        }
    }
    
    // Team filter change handler
    async onTeamChange(event) {
        const selectedOptions = Array.from(event.target.selectedOptions).map(option => parseInt(option.value));
        this.state.selectedTeams = selectedOptions;
        await this.applyFilters();
    }
    
    // Apply all filters
    async applyFilters() {
        try {
            this.state.loading = true;
            this.state.error = null; // Reset error state
            await this.fetchDashboardData();
        } catch (error) {
            console.error('Filter Application Error:', error);
            this.state.error = error.message || 'Failed to apply filters';
            this.notification.add(this.state.error, { 
                type: 'danger',
                sticky: false
            });
        } finally {
            this.state.loading = false;
        }
    }
    
    // Reset all filters
    async resetFilters() {
        this.state.selectedCategories = [];
        this.state.selectedTeams = [];
        this.state.customDateRange = false;
        this.state.period = 90;
        this.setDefaultDates();
        
        // Reset category filter cache
        this.categoryFilteredOrderIds = null;
        
        await this.applyFilters();
    }
    
    // Toggle filter panel visibility
    toggleFilters() {
        this.state.showFilters = !this.state.showFilters;
    }

    async getQuotations(current_date, previous_date, additionalFilters = []) {
        try {
            // Current period domain
            let domain = [
                ['state', 'in', ['sent', 'draft']],
                ['create_date', '>=', current_date],
                ['create_date', '<=', this.state.endDate]
            ];
            
            // Add additional filters
            domain = [...domain, ...additionalFilters];
            
            // Add category filters if needed
            const categoryOrderIds = await this.getCategoryFilteredOrderIds();
            if (categoryOrderIds !== null) {
                if (categoryOrderIds.length === 0) {
                    // No orders match the category filter, return empty results
                    this.state.quotations = { value: 0, percentage: 0 };
                    return;
                }
                // Add order IDs to the domain
                domain.push(['id', 'in', categoryOrderIds]);
            }
            
            const data = await this.orm.searchCount("sale.order", domain);
            
            // Previous period domain
            let prev_domain = [
                ['state', 'in', ['sent', 'draft']],
                ['create_date', '>=', previous_date],
                ['create_date', '<', current_date]
            ];
            
            // Add additional filters
            prev_domain = [...prev_domain, ...additionalFilters];
            
            // Add category filters if needed
            if (categoryOrderIds !== null) {
                prev_domain.push(['id', 'in', categoryOrderIds]);
            }
            
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
            this.state.quotations = { value: 0, percentage: 0 };
            throw error;
        }
    }

    async getOrders(current_date, previous_date, additionalFilters = []) {
        try {
            // Current period domain
            let domain = [
                ['state', 'in', ['sale', 'done']],
                ['create_date', '>=', current_date],
                ['create_date', '<=', this.state.endDate]
            ];
            
            // Add additional filters
            domain = [...domain, ...additionalFilters];
            
            // Add category filters if needed
            const categoryOrderIds = await this.getCategoryFilteredOrderIds();
            if (categoryOrderIds !== null) {
                if (categoryOrderIds.length === 0) {
                    // No orders match the category filter, return empty results
                    this.state.orders = {
                        value: 0, percentage: 0,
                        revenue: 0, revenue_percentage: 0,
                        average: 0, average_percentage: 0
                    };
                    return;
                }
                // Add order IDs to the domain
                domain.push(['id', 'in', categoryOrderIds]);
            }
            
            const data = await this.orm.searchCount("sale.order", domain);

            // Previous period domain
            let prev_domain = [
                ['state', 'in', ['sale', 'done']],
                ['create_date', '>=', previous_date],
                ['create_date', '<', current_date]
            ];
            
            // Add additional filters
            prev_domain = [...prev_domain, ...additionalFilters];
            
            // Add category filters if needed
            if (categoryOrderIds !== null) {
                prev_domain.push(['id', 'in', categoryOrderIds]);
            }
            
            const prev_data = await this.orm.searchCount("sale.order", prev_domain);

            const current_revenue = await this.orm.readGroup("sale.order", domain, ["amount_total:sum"], []);
            const prev_revenue = await this.orm.readGroup("sale.order", prev_domain, ["amount_total:sum"], []);

            const current_average = await this.orm.readGroup("sale.order", domain, ["amount_total:avg"], []);
            const prev_average = await this.orm.readGroup("sale.order", prev_domain, ["amount_total:avg"], []);

            const calculatePercentage = (current, previous) => 
                previous > 0 ? ((current - previous) / previous) * 100 : 0;

            const currentRevenueValue = current_revenue[0]?.amount_total || 0;
            const prevRevenueValue = prev_revenue[0]?.amount_total || 0;
            const currentAverageValue = current_average[0]?.amount_total || 0;
            const prevAverageValue = prev_average[0]?.amount_total || 0;

            this.state.orders = {
                value: data,
                percentage: calculatePercentage(data, prev_data).toFixed(2),
                revenue: currentRevenueValue,
                revenue_percentage: calculatePercentage(
                    currentRevenueValue, 
                    prevRevenueValue
                ).toFixed(2),
                average: currentAverageValue,
                average_percentage: calculatePercentage(
                    currentAverageValue, 
                    prevAverageValue
                ).toFixed(2)
            };
        } catch (error) {
            console.error('Orders Fetch Error:', error);
            this.state.orders = {
                value: 0, percentage: 0,
                revenue: 0, revenue_percentage: 0,
                average: 0, average_percentage: 0
            };
            throw error;
        }
    }

    async getTopProducts(current_date, additionalFilters = []) {
        try {
            // Determine which orders to include
            let orderDomain = [
                ['state', 'in', ['sale', 'done']],
                ['create_date', '>=', current_date],
                ['create_date', '<=', this.state.endDate]
            ];
            
            // Add additional filters
            orderDomain = [...orderDomain, ...additionalFilters];
            
            // Add category filters if needed
            let categoryOrderIds = await this.getCategoryFilteredOrderIds();
            if (categoryOrderIds !== null) {
                if (categoryOrderIds.length === 0) {
                    // No orders match the category filter, return empty results
                    this.state.topProducts = [];
                    return;
                }
                // Add order IDs to the domain
                orderDomain.push(['id', 'in', categoryOrderIds]);
            }
            
            // Get valid order IDs
            const orderIds = await this.orm.search('sale.order', orderDomain);
            
            if (!orderIds || orderIds.length === 0) {
                // No orders found
                this.state.topProducts = [];
                return;
            }
            
            // Get product data from order lines
            let lineDomain = [['order_id', 'in', orderIds]];
            
            // If categories selected and we didn't already filter by order IDs
            if (this.state.selectedCategories.length > 0 && categoryOrderIds === null) {
                lineDomain.push(['product_id.categ_id', 'in', this.state.selectedCategories]);
            }
            
            const data = await this.orm.readGroup(
                "sale.order.line", 
                lineDomain, 
                ["product_id", "price_total:sum"], 
                ["product_id"]
            );
            
            this.state.topProducts = data
                .filter(item => item.product_id) 
                .map(item => ({ 
                    label: item.product_id[1] || 'Unknown', 
                    value: item.price_total || 0 
                }))
                .sort((a, b) => b.value - a.value)
                .slice(0, 10);
        } catch (error) {
            console.error('Top Products Fetch Error:', error);
            this.state.topProducts = [];
            throw error;
        }
    }

    async getTopSalesPeople(current_date, additionalFilters = []) {
        try {
            let domain = [
                ['state', 'in', ['sale', 'done']],
                ['create_date', '>=', current_date],
                ['create_date', '<=', this.state.endDate]
            ];
            
            // Add additional filters
            domain = [...domain, ...additionalFilters];
            
            // Add category filters if needed
            const categoryOrderIds = await this.getCategoryFilteredOrderIds();
            if (categoryOrderIds !== null) {
                if (categoryOrderIds.length === 0) {
                    // No orders match the category filter, return empty results
                    this.state.topSalesPeople = [];
                    return;
                }
                // Add order IDs to the domain
                domain.push(['id', 'in', categoryOrderIds]);
            }
            
            const data = await this.orm.readGroup("sale.order", domain, 
                ["user_id", "amount_total:sum"], 
                ["user_id"]
            );
            
            this.state.topSalesPeople = data
                .filter(item => item.user_id)
                .map(item => ({ 
                    label: item.user_id[1] || 'Unknown', 
                    value: item.amount_total || 0 
                }))
                .sort((a, b) => b.value - a.value)
                .slice(0, 10);
        } catch (error) {
            console.error('Top Sales People Fetch Error:', error);
            this.state.topSalesPeople = [];
            throw error;
        }
    }

    async getMonthlySales(current_date, additionalFilters = []) {
        try {
            let domain = [
                ['state', 'in', ['sale', 'done']],
                ['create_date', '>=', current_date],
                ['create_date', '<=', this.state.endDate]
            ];
            
            // Add additional filters
            domain = [...domain, ...additionalFilters];
            
            // Add category filters if needed
            const categoryOrderIds = await this.getCategoryFilteredOrderIds();
            if (categoryOrderIds !== null) {
                if (categoryOrderIds.length === 0) {
                    // No orders match the category filter, return empty results
                    this.state.monthlySales = [];
                    return;
                }
                // Add order IDs to the domain
                domain.push(['id', 'in', categoryOrderIds]);
            }
            
            const data = await this.orm.readGroup("sale.order", domain, 
                ["amount_total:sum"], 
                ["create_date:month"]
            );
            
            // Format data for the chart
            this.state.monthlySales = data
                .map(item => {
                    // Find the month information from the available fields
                    let monthLabel = 'Unknown';
                    for (const key in item) {
                        if (key.includes('month') || key.includes('date')) {
                            if (item[key] && typeof item[key] === 'string') {
                                monthLabel = item[key];
                                break;
                            }
                        }
                    }
                    
                    return {
                        label: monthLabel,
                        value: Number(item.amount_total || 0)
                    };
                })
                .sort((a, b) => a.label.localeCompare(b.label))
                .slice(0, 12);
        } catch (error) {
            console.error('Monthly Sales Fetch Error:', error);
            this.state.monthlySales = [];
            throw error;
        }
    }

    async getPartnerOrders(current_date, additionalFilters = []) {
        try {
            let domain = [
                ['state', 'in', ['sale', 'done']],
                ['create_date', '>=', current_date],
                ['create_date', '<=', this.state.endDate]
            ];
            
            // Add additional filters
            domain = [...domain, ...additionalFilters];
            
            // Add category filters if needed
            const categoryOrderIds = await this.getCategoryFilteredOrderIds();
            if (categoryOrderIds !== null) {
                if (categoryOrderIds.length === 0) {
                    // No orders match the category filter, return empty results
                    this.state.partnerOrders = [];
                    return;
                }
                // Add order IDs to the domain
                domain.push(['id', 'in', categoryOrderIds]);
            }
            
            const data = await this.orm.readGroup("sale.order", domain, 
                ["partner_id", "amount_total:sum"], 
                ["partner_id"]
            );
            
            this.state.partnerOrders = data
                .filter(item => item.partner_id)
                .map(item => ({ 
                    label: item.partner_id[1] || 'Unknown', 
                    value: item.amount_total || 0 
                }))
                .sort((a, b) => b.value - a.value)
                .slice(0, 10);
        } catch (error) {
            console.error('Partner Orders Fetch Error:', error);
            this.state.partnerOrders = [];
            throw error;
        }
    }

    // Navigation actions
    viewQuotations() {
        const { current_date } = this.getDates();
        let domain = [
            ['state', 'in', ['sent', 'draft']],
            ['create_date', '>=', current_date],
            ['create_date', '<=', this.state.endDate]
        ];
        
        // Add filter domains
        domain = [...domain, ...this.buildDomainFilters()];

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Quotations",
            res_model: "sale.order",
            domain,
            views: [
                [false, "list"],
                [false, "form"],
            ]
        });
    }

    viewOrders() {
        const { current_date } = this.getDates();
        let domain = [
            ['state', 'in', ['sale', 'done']],
            ['create_date', '>=', current_date],
            ['create_date', '<=', this.state.endDate]
        ];
        
        // Add filter domains
        domain = [...domain, ...this.buildDomainFilters()];

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Orders",
            res_model: "sale.order",
            domain,
            views: [
                [false, "list"],
                [false, "form"],
            ]
        });
    }

    viewRevenues() {
        const { current_date } = this.getDates();
        let domain = [
            ['state', 'in', ['sale', 'done']],
            ['create_date', '>=', current_date],
            ['create_date', '<=', this.state.endDate]
        ];
        
        // Add filter domains
        domain = [...domain, ...this.buildDomainFilters()];

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
}

OwlSalesDashboard.template = "owl.OwlSalesDashboard";
OwlSalesDashboard.components = { KpiCard, ChartRenderer };

registry.category("actions").add("owl.sales_dashboard", OwlSalesDashboard);