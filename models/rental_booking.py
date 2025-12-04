from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class StockRentalBooking(models.Model):
    _name = 'stock.rental.booking'
    _description = 'Stock Rental Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'

    name = fields.Char(string="Booking Reference", required=True, copy=False, readonly=True, default=lambda self: _('New'))

    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    
    partner_id = fields.Many2one('res.partner', string="Customer", check_company=True)
    project_id = fields.Many2one('project.project', string="Project", check_company=True, required=True)

    source_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string="Source Warehouse",
        required=True,
        check_company=True,
    )
    rental_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string="Rental Warehouse",
        required=True,
        check_company=True,
    )

    source_location_id = fields.Many2one(
        'stock.location',
        string="Source Location",
        compute="_compute_locations",
        store=False,
    )
    rental_location_id = fields.Many2one(
        'stock.location',
        string="Rental Location",
        compute="_compute_locations",
        store=False,
    )
    
    def _compute_locations(self):
        for booking in self:
            source_location = False
            rental_location = False
            if booking.source_warehouse_id:
                source_location = booking.source_warehouse_id.lot_stock_id
            if booking.rental_warehouse_id:
                rental_location = booking.rental_warehouse_id.lot_stock_id
            booking.source_location_id = source_location
            booking.rental_location_id = rental_location
    
    date_start = fields.Datetime(string="Start Date", default=fields.Datetime.now, tracking=True)
    date_end = fields.Datetime(string="End Date", tracking=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('reserved', 'Reserved'),
        ('ongoing', 'Ongoing'),
        ('finished', 'Finished'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', tracking=True, group_expand='_expand_states')
    
    line_ids = fields.One2many('stock.rental.booking.line', 'booking_id', string="Lines")
    
    notes = fields.Text(string="Notes")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.rental.booking') or _('New')
        return super().create(vals_list)

    def action_confirm(self):
        for booking in self:
            # Validate header fields only when confirming
            if not booking.date_start:
                raise ValidationError(_("Start date is required."))
            if booking.date_start and not booking.date_end:
                raise ValidationError(_("End date is required."))
            if booking.date_start and booking.date_end and booking.date_start > booking.date_end:
                raise ValidationError(_("Start date cannot be after end date."))
            if not booking.project_id:
                raise ValidationError(_("Project is required for Rental bookings."))

            # Ensure all lines are complete and available when confirming
            for line in booking.line_ids:
                if not line.product_id:
                    raise ValidationError(_("Each line must have a product before confirming a booking."))
                if not line.source_warehouse_id or not line.rental_warehouse_id:
                    raise ValidationError(_("Each line must have both Source Warehouse and Rental Warehouse set."))
                line._check_line_availability()

            booking._create_start_picking()
            booking.state = 'reserved'

    def action_mark_ongoing(self):
        for booking in self:
            booking.state = 'ongoing'

    def action_finish(self):
        for booking in self:
            booking.state = 'finished'

    def action_return(self):
        for booking in self:
            booking._create_return_picking()
            booking.state = 'returned'

    def action_cancel(self):
        for booking in self:
            booking.state = 'cancelled'
            
    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    @api.model
    def _cron_update_booking_states(self):
        now = fields.Datetime.now()
        
        # Reserved -> should start
        bookings_to_start = self.search([
            ('state', '=', 'reserved'),
            ('date_start', '<=', now),
            ('date_end', '>', now)
        ])
        for booking in bookings_to_start:
            booking.message_post(body=_("Rental booking %s should start based on its planned dates.") % booking.name)
        
        # Reserved/Ongoing -> should be finished
        bookings_to_finish = self.search([
            ('state', 'in', ['reserved', 'ongoing']),
            ('date_end', '<=', now)
        ])
        for booking in bookings_to_finish:
            booking.message_post(body=_("Rental booking %s has passed its end date and should be finished/returned.") % booking.name)

    def _create_start_picking(self):
        Picking = self.env['stock.picking']
        Move = self.env['stock.move']
        for booking in self:
            lines_by_wh = {}
            for line in booking.line_ids:
                if not line.product_id or line.quantity <= 0:
                    continue
                if not line.source_warehouse_id or not line.rental_warehouse_id:
                    continue
                key = (line.source_warehouse_id.id, line.rental_warehouse_id.id)
                lines_by_wh.setdefault(key, []).append(line)

            for (source_wh_id, rental_wh_id), lines in lines_by_wh.items():
                source_wh = self.env['stock.warehouse'].browse(source_wh_id)
                rental_wh = self.env['stock.warehouse'].browse(rental_wh_id)
                source_location = source_wh.lot_stock_id
                rental_location = rental_wh.lot_stock_id
                if not source_location or not rental_location:
                    continue
                picking_type = source_wh.int_type_id
                if not picking_type:
                    continue
                picking_vals = {
                    'picking_type_id': picking_type.id,
                    'location_id': source_location.id,
                    'location_dest_id': rental_location.id,
                    'company_id': booking.company_id.id,
                    'origin': booking.name,
                    'rental_booking_id': booking.id,
                    'rental_direction': 'out',
                }
                picking = Picking.create(picking_vals)
                for line in lines:
                    Move.create({
                        'product_id': line.product_id.id,
                        'product_uom': line.product_id.uom_id.id,
                        'product_uom_qty': line.quantity,
                        'picking_id': picking.id,
                        'company_id': booking.company_id.id,
                        'location_id': source_location.id,
                        'location_dest_id': rental_location.id,
                    })
                picking.action_confirm()
                picking.action_assign()

    def _create_return_picking(self):
        Picking = self.env['stock.picking']
        Move = self.env['stock.move']
        for booking in self:
            lines_by_wh = {}
            for line in booking.line_ids:
                if not line.product_id or line.quantity <= 0:
                    continue
                if not line.source_warehouse_id or not line.rental_warehouse_id:
                    continue
                key = (line.source_warehouse_id.id, line.rental_warehouse_id.id)
                lines_by_wh.setdefault(key, []).append(line)

            for (source_wh_id, rental_wh_id), lines in lines_by_wh.items():
                source_wh = self.env['stock.warehouse'].browse(source_wh_id)
                rental_wh = self.env['stock.warehouse'].browse(rental_wh_id)
                source_location = source_wh.lot_stock_id
                rental_location = rental_wh.lot_stock_id
                if not source_location or not rental_location:
                    continue
                picking_type = rental_wh.int_type_id
                if not picking_type:
                    continue
                picking_vals = {
                    'picking_type_id': picking_type.id,
                    'location_id': rental_location.id,
                    'location_dest_id': source_location.id,
                    'company_id': booking.company_id.id,
                    'origin': booking.name,
                    'rental_booking_id': booking.id,
                    'rental_direction': 'in',
                }
                picking = Picking.create(picking_vals)
                for line in lines:
                    Move.create({
                        'product_id': line.product_id.id,
                        'product_uom': line.product_id.uom_id.id,
                        'product_uom_qty': line.quantity,
                        'picking_id': picking.id,
                        'company_id': booking.company_id.id,
                        'location_id': rental_location.id,
                        'location_dest_id': source_location.id,
                    })
                picking.action_confirm()
                picking.action_assign()


class StockRentalBookingLine(models.Model):
    _name = 'stock.rental.booking.line'
    _description = 'Stock Rental Booking Line'

    booking_id = fields.Many2one('stock.rental.booking', string="Booking", required=True, ondelete="cascade")
    company_id = fields.Many2one(related='booking_id.company_id', store=True)
    source_warehouse_id = fields.Many2one('stock.warehouse', string="Source Warehouse", check_company=True)
    rental_warehouse_id = fields.Many2one('stock.warehouse', string="Rental Warehouse", check_company=True)
    source_location_id = fields.Many2one('stock.location', string="Source Location", compute="_compute_locations", store=False)
    rental_location_id = fields.Many2one('stock.location', string="Rental Location", compute="_compute_locations", store=False)
    
    product_id = fields.Many2one('product.product', string="Product")
    quantity = fields.Float(string="Quantity", default=1.0, digits='Product Unit of Measure')
    
    date_start = fields.Datetime(related='booking_id.date_start', store=True)
    date_end = fields.Datetime(related='booking_id.date_end', store=True)
    state = fields.Selection(related='booking_id.state', store=True)

    @api.onchange('booking_id')
    def _onchange_booking_id(self):
        for line in self:
            if line.booking_id:
                if not line.source_warehouse_id:
                    line.source_warehouse_id = line.booking_id.source_warehouse_id
                if not line.rental_warehouse_id:
                    line.rental_warehouse_id = line.booking_id.rental_warehouse_id

    def _compute_locations(self):
        for line in self:
            source_location = False
            rental_location = False
            if line.source_warehouse_id:
                source_location = line.source_warehouse_id.lot_stock_id
            if line.rental_warehouse_id:
                rental_location = line.rental_warehouse_id.lot_stock_id
            line.source_location_id = source_location
            line.rental_location_id = rental_location

    def _check_line_availability(self):
        """
        Check if adding this line would exceed the product's rental_total_units
        during the booking period.
        """
        Quant = self.env['stock.quant']
        for line in self:
            if not line.product_id or not line.date_start or not line.date_end:
                continue

            if line.quantity <= 0:
                continue

            product = line.product_id
            company = line.company_id or self.env.company

            domain_quant = [
                ('product_id', '=', product.id),
                ('company_id', '=', company.id if company else False),
                ('location_id.usage', '=', 'internal'),
            ]

            groups = Quant.read_group(domain_quant, ['quantity:sum', 'reserved_quantity:sum'], [])
            if groups:
                quantity = groups[0].get('quantity', 0.0) or 0.0
                reserved_qty = groups[0].get('reserved_quantity', 0.0) or 0.0
                base_capacity = quantity - reserved_qty
            else:
                base_capacity = 0.0

            if base_capacity <= 0:
                raise ValidationError(_(
                    "No available stock for product '%s' in the selected warehouse."
                ) % (product.display_name,))

            domain = [
                ('id', '!=', line.id),
                ('product_id', '=', product.id),
                ('company_id', '=', company.id if company else False),
                ('state', 'in', ['reserved', 'ongoing']),
                ('date_start', '<', line.date_end),
                ('date_end', '>', line.date_start),
            ]
            overlapping_lines = self.search(domain)
            current_booked_qty = sum(overlapping_lines.mapped('quantity'))

            if current_booked_qty + line.quantity > base_capacity:
                raise ValidationError(_(
                    "Not enough availability for product '%s' during this period.\n"
                    "Available capacity: %s\n"
                    "Already booked: %s\n"
                    "Requested: %s"
                ) % (product.display_name, base_capacity, current_booked_qty, line.quantity))

    @api.constrains('product_id', 'date_start', 'date_end', 'state', 'company_id', 'quantity')
    def _constrains_check_availability(self):
        for line in self:
            if line.state in ['reserved', 'ongoing', 'finished']:
                line._check_line_availability()

    @api.model
    def get_availability_grid(
        self,
        product_ids,
        date_start,
        week_count=12,
        warehouse_id=None,
        company_id=None,
        needed_by_product=None,
    ):
        """Return a per-product, per-week availability grid for rentals.

        :param product_ids: list of product.product ids to include as rows.
        :param date_start: reference date (datetime or string); grid is aligned to the
            Monday of the week containing this date.
        :param week_count: number of weeks to include (capped internally).
        :param warehouse_id: optional stock.warehouse id used as source warehouse
            for capacity and booking-lines filtering.
        :param company_id: optional res.company id; defaults to current company.
        :param needed_by_product: optional dict {product_id: qty} used mainly for
            booking-specific views to highlight if capacity is sufficient.
        :return: dict with ``meta``, ``columns`` and ``rows`` suitable for OWL grids.
        """
        # Normalise inputs
        if not product_ids:
            product_ids = []
        elif isinstance(product_ids, int):
            product_ids = [product_ids]

        week_count = int(week_count or 0)
        if week_count <= 0:
            week_count = 12
        max_week_count = 20
        if week_count > max_week_count:
            week_count = max_week_count

        needed_by_product = needed_by_product or {}

        company = self.env['res.company'].browse(company_id) if company_id else self.env.company
        self = self.with_context(allowed_company_ids=[company.id])

        # Parse and normalise date_start, then align to Monday (ISO week)
        if date_start:
            base_dt = fields.Datetime.to_datetime(date_start)
        else:
            base_dt = fields.Datetime.now()

        base_date = base_dt.date()
        weekday = base_date.weekday()  # Monday = 0
        monday_date = base_date - timedelta(days=weekday)
        monday_dt = datetime.combine(monday_date, datetime.min.time())

        weeks = []
        for index in range(week_count):
            week_start_dt = monday_dt + timedelta(weeks=index)
            week_end_dt = week_start_dt + timedelta(days=7)
            iso_year, iso_week, _ = week_start_dt.isocalendar()
            column_key = f"{iso_year}-W{iso_week:02d}"
            weeks.append({
                'key': column_key,
                'label': f"V.{iso_week}",
                'start_dt': week_start_dt,
                'end_dt': week_end_dt,
            })

        if weeks:
            overall_start_dt = weeks[0]['start_dt']
            overall_end_dt = weeks[-1]['end_dt']
        else:
            # Should not happen with current week_count logic, but keep sane defaults.
            overall_start_dt = monday_dt
            overall_end_dt = monday_dt

        # Compute base capacity per product via stock.quant
        Quant = self.env['stock.quant']
        domain_quant = [
            ('product_id', 'in', product_ids),
            ('company_id', '=', company.id),
        ]
        if warehouse_id:
            warehouse = self.env['stock.warehouse'].browse(warehouse_id)
            if warehouse and warehouse.lot_stock_id:
                domain_quant.append(('location_id', 'child_of', warehouse.lot_stock_id.id))
            else:
                # Fall back to all internal locations if warehouse is misconfigured
                domain_quant.append(('location_id.usage', '=', 'internal'))
        else:
            domain_quant.append(('location_id.usage', '=', 'internal'))

        base_capacity_by_product = defaultdict(float)
        if product_ids:
            groups = Quant.read_group(
                domain_quant,
                ['product_id', 'quantity:sum', 'reserved_quantity:sum'],
                ['product_id'],
            )
            for group in groups:
                product_field = group.get('product_id')
                if isinstance(product_field, (list, tuple)):
                    product_id = product_field[0]
                else:
                    product_id = product_field
                if not product_id:
                    continue
                quantity = group.get('quantity', 0.0) or 0.0
                reserved_qty = group.get('reserved_quantity', 0.0) or 0.0
                base_capacity_by_product[product_id] = max(quantity - reserved_qty, 0.0)

        # Pre-compute booked quantities per product & week from booking lines
        booked_by_product_week = defaultdict(lambda: defaultdict(float))
        if product_ids and weeks:
            domain_lines = [
                ('product_id', 'in', product_ids),
                ('company_id', '=', company.id),
                ('state', 'in', ['reserved', 'ongoing']),
                ('date_start', '<', fields.Datetime.to_string(overall_end_dt)),
                ('date_end', '>', fields.Datetime.to_string(overall_start_dt)),
            ]
            if warehouse_id:
                domain_lines.append(('source_warehouse_id', '=', warehouse_id))

            lines = self.search(domain_lines)
            for line in lines:
                if not line.product_id:
                    continue
                pid = line.product_id.id
                line_start = fields.Datetime.to_datetime(line.date_start) if line.date_start else None
                line_end = fields.Datetime.to_datetime(line.date_end) if line.date_end else None
                if not line_start or not line_end:
                    continue
                for week in weeks:
                    ws = week['start_dt']
                    we = week['end_dt']
                    # Overlap check: [line_start, line_end) vs [ws, we)
                    if line_start < we and line_end > ws:
                        booked_by_product_week[pid][week['key']] += line.quantity

        # Build column descriptors for the frontend
        columns = []
        for week in weeks:
            columns.append({
                'key': week['key'],
                'label': week['label'],
                'start': fields.Datetime.to_string(week['start_dt']),
                'end': fields.Datetime.to_string(week['end_dt']),
            })

        # Build row data per product
        products = self.env['product.product'].browse(product_ids)
        rows = []
        for product in products:
            base_capacity = float(base_capacity_by_product.get(product.id, 0.0) or 0.0)
            needed = float(needed_by_product.get(product.id, 0.0) or 0.0)
            cells = []
            for week in weeks:
                week_key = week['key']
                booked = float(booked_by_product_week[product.id].get(week_key, 0.0) or 0.0)
                available = max(base_capacity - booked, 0.0)

                cell_needed = needed if needed > 0.0 else None
                status = 'free'
                booking_ok = None

                if cell_needed is not None:
                    if available >= cell_needed:
                        status = 'free'
                        booking_ok = True
                    elif available > 0.0:
                        status = 'partial'
                        booking_ok = False
                    else:
                        status = 'full'
                        booking_ok = False
                else:
                    if available <= 0.0:
                        status = 'full'
                    else:
                        status = 'free'

                try:
                    tooltip = _(
                        "Booked: %(booked)s, Available: %(available)s",
                        booked=booked,
                        available=available,
                    )
                except Exception:
                    tooltip = None

                cells.append({
                    'column_key': week_key,
                    'booked': booked,
                    'available': available,
                    'needed': cell_needed,
                    'status': status,
                    'booking_ok': booking_ok,
                    'tooltip': tooltip,
                })

            rows.append({
                'product_id': product.id,
                'display_name': product.display_name,
                'default_code': product.default_code,
                'uom_name': product.uom_id.name,
                'base_capacity': base_capacity,
                'needed': needed if needed > 0.0 else None,
                'cells': cells,
            })

        result = {
            'meta': {
                'company_id': company.id,
                'warehouse_id': warehouse_id,
                'date_start': fields.Datetime.to_string(overall_start_dt),
                'date_end': fields.Datetime.to_string(overall_end_dt),
                'week_count': week_count,
            },
            'columns': columns,
            'rows': rows,
        }
        return result
