/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// Cost Sheet Calculator Widget
class CostSheetCalculatorWidget extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        this.state = useState({
            isCalculating: false,
            lastCalculated: null,
            totals: {
                totalAmount: 0,
                enabledAmount: 0,
                totalArea: 0,
                ratePerSqm: 0
            }
        });
        
        onMounted(() => {
            this.updateTotals();
        });
    }
    
    async updateTotals() {
        if (!this.props.resId) return;
        
        try {
            const record = await this.orm.read("drkds.cost.sheet", [this.props.resId], [
                "total_amount", "enabled_components_total", "total_area", "rate_per_sqm"
            ]);
            
            if (record.length > 0) {
                this.state.totals = {
                    totalAmount: record[0].total_amount,
                    enabledAmount: record[0].enabled_components_total,
                    totalArea: record[0].total_area,
                    ratePerSqm: record[0].rate_per_sqm
                };
            }
        } catch (error) {
            console.error("Error updating totals:", error);
        }
    }
    
    async calculate() {
        if (!this.props.resId || this.state.isCalculating) return;
        
        this.state.isCalculating = true;
        
        try {
            await this.orm.call("drkds.cost.sheet", "action_calculate", [this.props.resId]);
            
            this.state.lastCalculated = new Date().toLocaleString();
            await this.updateTotals();
            
            this.notification.add("Cost sheet calculated successfully!", {
                type: "success",
            });
            
            // Trigger form reload to show updated values
            this.env.bus.trigger("do-action", {
                type: "ir.actions.client",
                tag: "reload"
            });
            
        } catch (error) {
            this.notification.add(`Calculation failed: ${error.message}`, {
                type: "danger",
            });
        } finally {
            this.state.isCalculating = false;
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
}

CostSheetCalculatorWidget.template = "drkds_kit_calculations.CostSheetCalculatorWidget";
CostSheetCalculatorWidget.props = {
    resId: { type: Number, optional: true },
    readonly: { type: Boolean, optional: true }
};

registry.category("view_widgets").add("cost_sheet_calculator", CostSheetCalculatorWidget);

// Component Toggle Widget
class ComponentToggleWidget extends Component {
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
            await this.orm.call("drkds.cost.bom.line", "toggle_component", [this.props.resId]);
            
            // Trigger record reload
            this.env.bus.trigger("do-action", {
                type: "ir.actions.client",
                tag: "reload"
            });
            
        } catch (error) {
            this.notification.add(`Toggle failed: ${error.message}`, {
                type: "danger",
            });
        } finally {
            this.state.isToggling = false;
        }
    }
    
    get buttonClass() {
        const baseClass = "drkds_toggle_btn";
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

ComponentToggleWidget.template = "drkds_kit_calculations.ComponentToggleWidget";
ComponentToggleWidget.props = {
    resId: { type: Number },
    isEnabled: { type: Boolean },
    isMandatory: { type: Boolean, optional: true },
    readonly: { type: Boolean, optional: true }
};

registry.category("view_widgets").add("component_toggle", ComponentToggleWidget);

// Template Preview Widget
class TemplatePreviewWidget extends Component {
    setup() {
        this.orm = useService("orm");
        
        this.state = useState({
            template: null,
            components: [],
            parameters: [],
            loading: false
        });
        
        onMounted(() => {
            if (this.props.templateId) {
                this.loadTemplate();
            }
        });
    }
    
    async loadTemplate() {
        if (!this.props.templateId || this.state.loading) return;
        
        this.state.loading = true;
        
        try {
            // Load template details
            const template = await this.orm.read("drkds.cost.template", [this.props.templateId], [
                "name", "description", "template_type", "component_count", "parameter_count"
            ]);
            
            if (template.length > 0) {
                this.state.template = template[0];
                
                // Load components
                const components = await this.orm.searchRead("drkds.template.component", [
                    ["template_id", "=", this.props.templateId]
                ], ["component_name", "default_enabled", "is_mandatory", "sequence"]);
                
                this.state.components = components.sort((a, b) => a.sequence - b.sequence);
                
                // Load parameters  
                const parameters = await this.orm.searchRead("drkds.template.parameter", [
                    ["template_id", "=", this.props.templateId]
                ], ["name", "parameter_type", "required", "sequence"]);
                
                this.state.parameters = parameters.sort((a, b) => a.sequence - b.sequence);
            }
        } catch (error) {
            console.error("Error loading template:", error);
        } finally {
            this.state.loading = false;
        }
    }
    
    get templateTypeDisplay() {
        const types = {
            'nvph_8x4': 'NVPH 8x4',
            'nvph_9x4': 'NVPH 9.6x4', 
            'rack_pinion': 'Rack and Pinion',
            'custom': 'Custom'
        };
        return types[this.state.template?.template_type] || 'Unknown';
    }
}

TemplatePreviewWidget.template = "drkds_kit_calculations.TemplatePreviewWidget";
TemplatePreviewWidget.props = {
    templateId: { type: Number, optional: true }
};

registry.category("view_widgets").add("template_preview", TemplatePreviewWidget);

// Real-time Calculation Mixin
export const RealTimeCalculationMixin = {
    setup() {
        this._super?.setup?.();
        this.calculationTimer = null;
    },
    
    scheduleCalculation(delay = 1000) {
        if (this.calculationTimer) {
            clearTimeout(this.calculationTimer);
        }
        
        this.calculationTimer = setTimeout(() => {
            this.performCalculation();
        }, delay);
    },
    
    async performCalculation() {
        if (!this.props.resId) return;
        
        try {
            await this.orm.call("drkds.cost.sheet", "_calculate_all_formulas", [this.props.resId]);
            this.trigger('calculation-complete');
        } catch (error) {
            console.error("Auto-calculation failed:", error);
        }
    },
    
    onDestroy() {
        if (this.calculationTimer) {
            clearTimeout(this.calculationTimer);
        }
        this._super?.onDestroy?.();
    }
};

// Utility Functions
export const CostSheetUtils = {
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
    }
};

// Global event handlers for component interactions
document.addEventListener('DOMContentLoaded', function() {
    // Handle component toggle clicks
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('drkds_component_toggle')) {
            e.preventDefault();
            const bomLineId = e.target.dataset.bomLineId;
            if (bomLineId) {
                toggleBOMComponent(parseInt(bomLineId));
            }
        }
    });
    
    // Handle parameter changes with debouncing
    const debouncedCalculate = CostSheetUtils.debounce(function(costSheetId) {
        triggerRecalculation(costSheetId);
    }, 1500);
    
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('drkds_parameter_input')) {
            const costSheetId = e.target.dataset.costSheetId;
            if (costSheetId) {
                debouncedCalculate(parseInt(costSheetId));
            }
        }
    });
});

async function toggleBOMComponent(bomLineId) {
    try {
        const result = await odoo.jsonRpc('/web/dataset/call_kw', {
            model: 'drkds.cost.bom.line',
            method: 'toggle_component',
            args: [bomLineId],
            kwargs: {}
        });
        
        // Reload the form view
        location.reload();
        
    } catch (error) {
        console.error('Toggle failed:', error);
    }
}

async function triggerRecalculation(costSheetId) {
    try {
        await odoo.jsonRpc('/web/dataset/call_kw', {
            model: 'drkds.cost.sheet',
            method: '_calculate_all_formulas', 
            args: [costSheetId],
            kwargs: {}
        });
        
        // Update totals in UI without full reload
        updateTotalsDisplay(costSheetId);
        
    } catch (error) {
        console.error('Auto-calculation failed:', error);
    }
}

async function updateTotalsDisplay(costSheetId) {
    try {
        const record = await odoo.jsonRpc('/web/dataset/call_kw', {
            model: 'drkds.cost.sheet',
            method: 'read',
            args: [costSheetId, ['total_amount', 'enabled_components_total', 'rate_per_sqm']],
            kwargs: {}
        });
        
        if (record && record.length > 0) {
            const data = record[0];
            
            // Update summary cards if they exist
            const totalAmountEl = document.querySelector('[data-field="enabled_components_total"]');
            const ratePerSqmEl = document.querySelector('[data-field="rate_per_sqm"]');
            
            if (totalAmountEl) {
                totalAmountEl.textContent = CostSheetUtils.formatCurrency(data.enabled_components_total);
            }
            
            if (ratePerSqmEl) {
                ratePerSqmEl.textContent = CostSheetUtils.formatCurrency(data.rate_per_sqm);
            }
        }
        
    } catch (error) {
        console.error('Failed to update totals:', error);
    }
}