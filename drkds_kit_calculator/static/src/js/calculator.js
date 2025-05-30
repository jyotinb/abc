/** @odoo-module **/
// File: drkds_kit_calculator/static/src/js/calculator.js

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// Kit Calculator Main Widget
class KitCalculatorWidget extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
        
        this.state = useState({
            isCalculating: false,
            lastCalculated: null,
            totals: {
                totalAmount: 0,
                enabledAmount: 0,
                totalArea: 0,
                ratePerSqm: 0
            },
            components: [],
            parameters: []
        });
        
        onMounted(() => {
            this.loadData();
            this.addCustomStyles();
        });
        
        onWillUnmount(() => {
            this.removeCustomStyles();
        });
    }
    
    addCustomStyles() {
        if (!document.getElementById('kit-calculator-styles')) {
            const style = document.createElement('style');
            style.id = 'kit-calculator-styles';
            style.textContent = `
                .kit_calculator_widget {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }
                .kit_summary_display {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }
                .kit_summary_item {
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    padding: 20px;
                    border-radius: 12px;
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }
                .kit_summary_value {
                    font-size: 24px;
                    font-weight: 700;
                    margin-bottom: 5px;
                }
                .kit_summary_label {
                    font-size: 12px;
                    opacity: 0.9;
                    text-transform: uppercase;
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    removeCustomStyles() {
        const style = document.getElementById('kit-calculator-styles');
        if (style) {
            style.remove();
        }
    }
    
    async loadData() {
        if (!this.props.resId) return;
        
        try {
            const record = await this.orm.read("kit.cost.sheet", [this.props.resId], [
                "total_amount", "enabled_amount", "total_area", "rate_per_sqm"
            ]);
            
            if (record.length > 0) {
                this.state.totals = {
                    totalAmount: record[0].total_amount,
                    enabledAmount: record[0].enabled_amount,
                    totalArea: record[0].total_area,
                    ratePerSqm: record[0].rate_per_sqm
                };
            }
            
            // Load components
            const components = await this.orm.searchRead("kit.cost.line", [
                ["cost_sheet_id", "=", this.props.resId]
            ], ["component_name", "is_enabled", "quantity", "rate", "amount"]);
            
            this.state.components = components;
            
        } catch (error) {
            console.error("Error loading data:", error);
        }
    }
    
    async calculate() {
        if (!this.props.resId || this.state.isCalculating) return;
        
        this.state.isCalculating = true;
        
        try {
            await this.orm.call("kit.cost.sheet", "action_calculate", [this.props.resId]);
            
            this.state.lastCalculated = new Date().toLocaleString();
            await this.loadData();
            
            this.notification.add("Calculation completed successfully!", {
                type: "success",
            });
            
            // Trigger form reload
            this.trigger('reload-record');
            
        } catch (error) {
            this.notification.add(`Calculation failed: ${error.message}`, {
                type: "danger",
            });
        } finally {
            this.state.isCalculating = false;
        }
    }
    
    async toggleComponent(componentId) {
        try {
            await this.orm.call("kit.cost.line", "toggle_component", [componentId]);
            await this.loadData();
            this.trigger('reload-record');
        } catch (error) {
            this.notification.add(`Toggle failed: ${error.message}`, {
                type: "danger",
            });
        }
    }
    
    formatCurrency(value) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 2
        }).format(value || 0);
    }
    
    formatNumber(value, decimals = 2) {
        return new Intl.NumberFormat('en-IN', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value || 0);
    }
    
    openWizard() {
        this.action.doAction({
            name: "Create Cost Sheet",
            type: "ir.actions.act_window",
            res_model: "kit.cost.calculator.wizard",
            view_mode: "form",
            target: "new"
        });
    }
}

KitCalculatorWidget.template = "drkds_kit_calculator.KitCalculatorWidget";
KitCalculatorWidget.props = {
    resId: { type: Number, optional: true },
    readonly: { type: Boolean, optional: true }
};

registry.category("view_widgets").add("kit_calculator", KitCalculatorWidget);

// Component Toggle Widget
class KitComponentToggle extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        this.state = useState({
            isToggling: false
        });
    }
    
    async toggleComponent() {
        if (!this.props.resId || this.state.isToggling) return;
        
        this.state.isToggling = true;
        
        try {
            await this.orm.call("kit.cost.line", "toggle_component", [this.props.resId]);
            
            this.trigger('component-toggled');
            
        } catch (error) {
            this.notification.add(`Toggle failed: ${error.message}`, {
                type: "danger",
            });
        } finally {
            this.state.isToggling = false;
        }
    }
    
    get buttonClass() {
        const baseClass = "kit_component_toggle";
        const stateClass = this.props.isEnabled ? "enabled" : "disabled";
        return `${baseClass} ${stateClass}`;
    }
    
    get buttonText() {
        return this.props.isEnabled ? "Enabled" : "Disabled";
    }
    
    get buttonIcon() {
        return this.props.isEnabled ? "fa-toggle-on" : "fa-toggle-off";
    }
}

KitComponentToggle.template = "drkds_kit_calculator.KitComponentToggle";
KitComponentToggle.props = {
    resId: { type: Number },
    isEnabled: { type: Boolean },
    isMandatory: { type: Boolean, optional: true },
    readonly: { type: Boolean, optional: true }
};

registry.category("view_widgets").add("kit_component_toggle", KitComponentToggle);

// Utility Functions
export const KitCalculatorUtils = {
    formatCurrency(value, currency = 'INR') {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2
        }).format(value || 0);
    },
    
    formatNumber(value, decimals = 2) {
        return new Intl.NumberFormat('en-IN', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value || 0);
    },
    
    calculatePercentage(part, total) {
        if (!total || total === 0) return 0;
        return (part / total) * 100;
    },
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    formatDate(date) {
        return new Intl.DateTimeFormat('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    }
};

// Real-time calculation functionality
class RealTimeCalculator {
    constructor(costSheetId, orm) {
        this.costSheetId = costSheetId;
        this.orm = orm;
        this.debounceTime = 1500;
        this.debouncedCalculate = KitCalculatorUtils.debounce(
            this.performCalculation.bind(this), 
            this.debounceTime
        );
    }
    
    scheduleCalculation() {
        this.debouncedCalculate();
    }
    
    async performCalculation() {
        if (!this.costSheetId) return;
        
        try {
            await this.orm.call("kit.cost.sheet", "_calculate_all_formulas", [this.costSheetId]);
            console.log('Auto-calculation completed');
        } catch (error) {
            console.error("Auto-calculation failed:", error);
        }
    }
}

// Global event handlers
document.addEventListener('DOMContentLoaded', function() {
    // Handle component toggle clicks
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('kit_component_toggle')) {
            e.preventDefault();
            const componentId = parseInt(e.target.dataset.componentId);
            if (componentId) {
                toggleKitComponent(componentId);
            }
        }
    });
    
    // Handle parameter changes with auto-calculation
    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('kit_parameter_input')) {
            const costSheetId = parseInt(e.target.dataset.costSheetId);
            if (costSheetId && window.kitCalculator) {
                window.kitCalculator.scheduleCalculation();
            }
        }
    });
});

// Global functions for server-side integration
async function toggleKitComponent(componentId) {
    try {
        const result = await odoo.jsonRpc('/web/dataset/call_kw', {
            model: 'kit.cost.line',
            method: 'toggle_component',
            args: [componentId],
            kwargs: {}
        });
        
        // Refresh the view
        if (window.location.reload) {
            window.location.reload();
        }
        
    } catch (error) {
        console.error('Component toggle failed:', error);
        if (window.odoo && window.odoo.notification) {
            window.odoo.notification.add('Toggle failed: ' + error.message, {
                type: 'danger'
            });
        }
    }
}

async function calculateKitCostSheet(costSheetId) {
    try {
        await odoo.jsonRpc('/web/dataset/call_kw', {
            model: 'kit.cost.sheet',
            method: 'action_calculate',
            args: [costSheetId],
            kwargs: {}
        });
        
        // Update UI elements
        updateKitTotalsDisplay(costSheetId);
        
        if (window.odoo && window.odoo.notification) {
            window.odoo.notification.add('Calculation completed successfully!', {
                type: 'success'
            });
        }
        
    } catch (error) {
        console.error('Calculation failed:', error);
        if (window.odoo && window.odoo.notification) {
            window.odoo.notification.add('Calculation failed: ' + error.message, {
                type: 'danger'
            });
        }
    }
}

async function updateKitTotalsDisplay(costSheetId) {
    try {
        const record = await odoo.jsonRpc('/web/dataset/call_kw', {
            model: 'kit.cost.sheet',
            method: 'read',
            args: [costSheetId, ['total_amount', 'enabled_amount', 'rate_per_sqm', 'total_area']],
            kwargs: {}
        });
        
        if (record && record.length > 0) {
            const data = record[0];
            
            // Update summary displays
            const totalAmountEl = document.querySelector('[data-field="enabled_amount"]');
            const ratePerSqmEl = document.querySelector('[data-field="rate_per_sqm"]');
            const totalAreaEl = document.querySelector('[data-field="total_area"]');
            
            if (totalAmountEl) {
                totalAmountEl.textContent = KitCalculatorUtils.formatCurrency(data.enabled_amount);
            }
            
            if (ratePerSqmEl) {
                ratePerSqmEl.textContent = KitCalculatorUtils.formatCurrency(data.rate_per_sqm);
            }
            
            if (totalAreaEl) {
                totalAreaEl.textContent = KitCalculatorUtils.formatNumber(data.total_area, 2) + ' m²';
            }
            
            // Add animation effect
            [totalAmountEl, ratePerSqmEl, totalAreaEl].forEach(el => {
                if (el) {
                    el.classList.add('kit_pulse');
                    setTimeout(() => el.classList.remove('kit_pulse'), 2000);
                }
            });
        }
        
    } catch (error) {
        console.error('Failed to update totals:', error);
    }
}

// Initialize global calculator instance when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize real-time calculator if cost sheet ID is available
    const costSheetId = document.querySelector('[data-cost-sheet-id]')?.dataset.costSheetId;
    if (costSheetId && window.odoo) {
        window.kitCalculator = new RealTimeCalculator(parseInt(costSheetId), window.odoo);
    }
});

// Export for use in other modules
export { 
    KitCalculatorWidget, 
    KitComponentToggle, 
    KitCalculatorUtils, 
    RealTimeCalculator 
};