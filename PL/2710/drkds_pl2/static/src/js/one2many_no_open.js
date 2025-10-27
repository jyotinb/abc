// File: your_module/static/src/js/one2many_no_open.js
odoo.define('your_module.one2many_no_open', function (require) {
    'use strict';

    const registry = require('web.field_registry');
    const One2ManyList = require('web.relational_fields').FieldOne2Many;

    const FieldOne2ManyNoOpen = One2ManyList.extend({
        // override the renderer to pass no_open to only this widget
        init() {
            this._super.apply(this, arguments);
            this.nodeOptions.no_open = true;
        },
    });

    registry.add('one2many_no_open', FieldOne2ManyNoOpen);
});
