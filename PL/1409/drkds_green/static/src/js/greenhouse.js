/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { registry } from "@web/core/registry";

export class GreenhouseFormController extends FormController {
    setup() {
        super.setup();
    }

    async onComponentCalculated() {
        this.notification.add("Components calculated successfully!", {
            type: "success",
        });
        await this.model.root.load();
        this.render();
    }
}

// Register the custom controller if needed
// registry.category("form_controllers").add("greenhouse_form", GreenhouseFormController);