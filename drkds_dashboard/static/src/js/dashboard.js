/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, useRef } from "@odoo/owl";

class DrkdsDashboard extends Component {
    setup() {
        this.state = useState({
            templates: [],
            currentTemplateId: null,
            dashboardData: {},
        });
        
        this.orm = useService("orm");
        this.rpc = useService("rpc");
        this.action = useService("action");
        this.templateSelectorRef = useRef("templateSelector");
        this.metricsContainerRef = useRef("metricsContainer");
        
        onWillStart(async () => {
            await this.loadTemplates();
        });
    }
    
    async loadTemplates() {
        const templates = await this.orm.searchRead(
            'drkds.dashboard.template',
            [],
            ['id', 'name']
        );
        
        this.state.templates = templates;
        
        if (templates.length) {
            this.state.currentTemplateId = templates[0].id;
            await this.loadDashboardData();
        }
    }
    
    async loadDashboardData() {
        if (!this.state.currentTemplateId) return;
        
        try {
            const result = await this.rpc({
                route: '/drkds_dashboard/get_metrics',
                params: { template_id: this.state.currentTemplateId }
            });
            
            if (result.success) {
                this.state.dashboardData = result.data;
            } else {
                this.showError(result.error);
            }
        } catch (error) {
            this.showError(error.toString());
        }
    }
    
    async onTemplateChange(ev) {
        this.state.currentTemplateId = parseInt(ev.target.value);
        await this.loadDashboardData();
    }
    
    async onExportClick(ev) {
        const exportFormat = ev.target.dataset.format;
        
        try {
            const result = await this.rpc({
                route: '/drkds_dashboard/export',
                params: {
                    template_id: this.state.currentTemplateId,
                    format: exportFormat
                }
            });
            
            if (result.success) {
                this.triggerFileDownload(
                    result.filename,
                    result.file_content,
                    result.export_format
                );
            } else {
                this.showError(result.error);
            }
        } catch (error) {
            this.showError(error.toString());
        }
    }
    
    triggerFileDownload(filename, content, format) {
        const blob = new Blob([content], {
            type: this.getMimeType(format)
        });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.click();
    }
    
    getMimeType(format) {
        const mimeTypes = {
            'csv': 'text/csv',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'pdf': 'application/pdf',
            'json': 'application/json'
        };
        return mimeTypes[format] || 'application/octet-stream';
    }
    
    showError(error) {
        console.error("Dashboard error:", error);
        // Show notification using UI Service in Odoo 17
    }
}

DrkdsDashboard.template = 'drkds_dashboard_template';

// Register the component with the action registry
registry.category("actions").add("drkds_dashboard", DrkdsDashboard);