/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

const actionRegistry = registry.category("actions");

export class RentalAvailabilityAction extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loading: true,
            error: null,
            grid: null,
        });

        onWillStart(async () => {
            await this.loadGrid();
        });
    }

    async loadGrid() {
        this.state.loading = true;
        this.state.error = null;
        try {
            // First version: include all products; we can narrow the domain later
            const productDomain = [];
            const products = await this.orm.searchRead(
                "product.product",
                productDomain,
                ["id"]
            );
            const productIds = products.map((p) => p.id);

            const grid = await this.orm.call(
                "stock.rental.booking.line",
                "get_availability_grid",
                [productIds],
                {
                    date_start: null,
                    week_count: 12,
                    warehouse_id: null,
                    needed_by_product: {},
                }
            );

            this.state.grid = grid;
        } catch (error) {
            // Basic error handling; frontend can be improved later
            // eslint-disable-next-line no-console
            console.error("Failed to load rental availability grid", error);
            this.state.error = error && error.message ? error.message : String(error);
        } finally {
            this.state.loading = false;
        }
    }

    openProduct(row) {
        if (!row || !row.product_id) {
            return;
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "product.product",
            res_id: row.product_id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    get columns() {
        return (this.state.grid && this.state.grid.columns) || [];
    }

    get rows() {
        return (this.state.grid && this.state.grid.rows) || [];
    }
}

RentalAvailabilityAction.template = "tl_rental_manager.RentalAvailabilityAction";

actionRegistry.add("stock_rental_availability_global", RentalAvailabilityAction);
