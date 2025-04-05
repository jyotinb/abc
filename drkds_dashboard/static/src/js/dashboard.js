odoo.define('drkds_dashboard.Dashboard', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;
    var rpc = require('web.rpc');

    var DrkdsDashboard = AbstractAction.extend({
        template: 'drkds_dashboard_template',
        
        events: {
            'change .o_drkds_template_selector': '_onTemplateChange',
            'click .o_drkds_export_btn': '_onExportClick'
        },

        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.dashboardData = {};
            this.templates = [];
            this.currentTemplateId = null;
        },

        willStart: function () {
            return this._loadTemplates();
        },

        start: function () {
            this._renderDashboard();
            return this._super.apply(this, arguments);
        },

        _loadTemplates: function () {
            var self = this;
            return rpc.query({
                model: 'drkds.dashboard.template',
                method: 'search_read',
                fields: ['id', 'name']
            }).then(function (templates) {
                self.templates = templates;
                return templates;
            });
        },

        _renderDashboard: function () {
            var $templateSelector = this.$('.o_drkds_template_selector');
            $templateSelector.empty();

            // Populate template selector
            this.templates.forEach(function (template) {
                $templateSelector.append(
                    $('<option>', {
                        value: template.id,
                        text: template.name
                    })
                );
            });

            // Load first template if available
            if (this.templates.length) {
                this.currentTemplateId = this.templates[0].id;
                $templateSelector.val(this.currentTemplateId);
                this._loadDashboardData();
            }
        },

        _loadDashboardData: function () {
            var self = this;
            if (!this.currentTemplateId) return;

            rpc.query({
                route: '/drkds_dashboard/get_metrics',
                params: {
                    template_id: this.currentTemplateId
                }
            }).then(function (result) {
                if (result.success) {
                    self.dashboardData = result.data;
                    self._renderMetrics();
                } else {
                    self._showError(result.error);
                }
            }).catch(function (error) {
                self._showError(error);
            });
        },

        _renderMetrics: function () {
            var $metricsContainer = this.$('.o_drkds_metrics_container');
            $metricsContainer.empty();

            // Render metrics
            Object.entries(this.dashboardData.metrics || {}).forEach(function (entry) {
                var [metricName, metricValue] = entry;
                $metricsContainer.append(
                    $('<div>', {
                        'class': 'o_drkds_metric_card',
                        'html': `
                            <div class="o_drkds_metric_title">${metricName}</div>
                            <div class="o_drkds_metric_value">${metricValue}</div>
                        `
                    })
                );
            });
        },

        _onTemplateChange: function (ev) {
            this.currentTemplateId = $(ev.currentTarget).val();
            this._loadDashboardData();
        },

        _onExportClick: function (ev) {
            var self = this;
            var exportFormat = $(ev.currentTarget).data('format');

            rpc.query({
                route: '/drkds_dashboard/export',
                params: {
                    template_id: this.currentTemplateId,
                    format: exportFormat
                }
            }).then(function (result) {
                if (result.success) {
                    self._triggerFileDownload(
                        result.filename, 
                        result.file_content, 
                        result.export_format
                    );
                } else {
                    self._showError(result.error);
                }
            }).catch(function (error) {
                self._showError(error);
            });
        },

        _triggerFileDownload: function (filename, content, format) {
            var blob = new Blob([content], {
                type: this._getMimeType(format)
            });
            var link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            link.click();
        },

        _getMimeType: function (format) {
            var mimeTypes = {
                'csv': 'text/csv',
                'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'pdf': 'application/pdf',
                'json': 'application/json'
            };
            return mimeTypes[format] || 'application/octet-stream';
        },

        _showError: function (error) {
            this.do_warn('Error', error);
        }
    });

    core.action_registry.add('drkds_dashboard', DrkdsDashboard);
    return DrkdsDashboard;
});