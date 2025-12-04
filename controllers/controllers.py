from odoo import http
from odoo.http import request


class StockRentalAvailabilityController(http.Controller):

    @http.route(
        '/stock_rental/availability_grid/global',
        type='json',
        auth='user'
    )
    def stock_rental_availability_global(
        self,
        company_id=None,
        warehouse_id=None,
        date_start=None,
        week_count=12,
        product_domain=None,
    ):
        env = request.env

        if company_id:
            try:
                company_id = int(company_id)
            except (TypeError, ValueError):
                company_id = None

        company = env.company
        if company_id:
            company = env['res.company'].browse(company_id)

        line_model = env['stock.rental.booking.line'].with_context(
            allowed_company_ids=[company.id]
        )

        week_count = int(week_count or 0)
        if week_count <= 0:
            week_count = 12

        if warehouse_id:
            try:
                warehouse_id = int(warehouse_id)
            except (TypeError, ValueError):
                warehouse_id = None

        if not product_domain:
            product_domain = [('type', '=', 'product')]

        products = env['product.product'].search(product_domain)
        product_ids = products.ids

        grid = line_model.get_availability_grid(
            product_ids=product_ids,
            date_start=date_start,
            week_count=week_count,
            warehouse_id=warehouse_id,
            company_id=company.id,
            needed_by_product=None,
        )

        grid.setdefault('meta', {})
        grid['meta'].setdefault('mode', 'global')
        return grid

    @http.route(
        '/stock_rental/availability_grid/booking',
        type='json',
        auth='user'
    )
    def stock_rental_availability_booking(
        self,
        booking_id,
        week_count=12,
        anchor='booking_period',
        date_start=None,
        warehouse_id=None,
    ):
        env = request.env

        try:
            booking_id = int(booking_id)
        except (TypeError, ValueError):
            return {'error': 'invalid_booking_id'}

        booking = env['stock.rental.booking'].browse(booking_id)
        if not booking.exists():
            return {'error': 'booking_not_found'}

        company = booking.company_id
        line_model = env['stock.rental.booking.line'].with_context(
            allowed_company_ids=[company.id]
        )

        week_count = int(week_count or 0)
        if week_count <= 0:
            week_count = 12

        if warehouse_id:
            try:
                warehouse_id = int(warehouse_id)
            except (TypeError, ValueError):
                warehouse_id = None

        if not warehouse_id:
            warehouse_id = booking.source_warehouse_id.id or None

        if anchor == 'booking_period' and not date_start:
            date_start = booking.date_start or booking.date_end

        needed_by_product = {}
        product_ids = []
        for line in booking.line_ids:
            if not line.product_id:
                continue
            pid = line.product_id.id
            qty = line.quantity or 0.0
            if pid not in needed_by_product:
                needed_by_product[pid] = 0.0
                product_ids.append(pid)
            needed_by_product[pid] += qty

        grid = line_model.get_availability_grid(
            product_ids=product_ids,
            date_start=date_start,
            week_count=week_count,
            warehouse_id=warehouse_id,
            company_id=company.id,
            needed_by_product=needed_by_product,
        )

        grid_meta = grid.setdefault('meta', {})
        grid_meta['mode'] = 'booking'
        grid_meta['booking_id'] = booking.id
        return grid
