/** @odoo-module **/

import { registry } from "@web/core/registry";
import { BookingAvailabilityWizard } from "./booking_availability_wizard";

/**
 * Client action handler that opens the BookingAvailabilityWizard dialog.
 * This is just a date picker - dates are only written to the form (not saved to DB)
 * until the user clicks Confirm on the booking itself.
 */
async function openBookingAvailabilityWizard(env, action) {
    const dialogService = env.services.dialog;
    const orm = env.services.orm;
    const actionService = env.services.action;
    
    const params = action.params || {};
    const bookingId = params.booking_id;
    const bookingLines = params.booking_lines || [];
    const warehouseId = params.warehouse_id;
    const companyId = params.company_id;

    const reloadBookingForm = (newDates = null) => {
        // Restore the booking form view, optionally with new dates in context
        const actionDef = {
            type: "ir.actions.act_window",
            res_model: "tl.rental.booking",
            res_id: bookingId,
            views: [[false, "form"]],
            target: "current",
        };
        
        if (newDates) {
            // Pass dates via context so the form can pick them up
            actionDef.context = {
                default_date_start: newDates.dateStart,
                default_date_end: newDates.dateEnd,
            };
        }
        
        actionService.doAction(actionDef, { clearBreadcrumbs: false });
    };

    dialogService.add(BookingAvailabilityWizard, {
        bookingId,
        bookingLines,
        warehouseId,
        companyId,
        onConfirm: async ({ dateStart, dateEnd }) => {
            if (bookingId && dateStart && dateEnd) {
                // Write dates with context to skip tracking (no chatter log)
                await orm.call("tl.rental.booking", "write", [[bookingId], {
                    date_start: dateStart,
                    date_end: dateEnd,
                }], { context: { tlrm_skip_date_tracking: true } });
            }
            reloadBookingForm();
        },
        close: () => {
            // Reload form when dialog is closed (X button, Cancel, or ESC)
            reloadBookingForm();
        },
    });
}

// Register the client action
registry.category("actions").add("tlrm_open_booking_availability_wizard", openBookingAvailabilityWizard);
