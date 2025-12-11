from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    tlrm_price_hour = fields.Monetary(string="Rental Price per Hour")
    tlrm_price_day = fields.Monetary(string="Rental Price per Day")
    tlrm_price_week = fields.Monetary(string="Rental Price per Week")
    
    tlrm_min_hours = fields.Float(string="Min. Rental Hours", default=1.0)
    tlrm_min_days = fields.Float(string="Min. Rental Days", default=0.0)
    tlrm_min_weeks = fields.Float(string="Min. Rental Weeks", default=0.0)
    
    tlrm_fleet_capacity = fields.Float(
        string="Fleet Capacity",
        default=0.0,
        help="Total units owned for rental. This is the theoretical maximum "
             "available for booking, regardless of current physical location. "
             "Used for availability calculations when items are out on rental."
    )
    
    tlrm_reserved_units = fields.Integer(
        string="Reserved Units", 
        compute="_compute_tlrm_counts", 
        store=False,
        help="Units reserved in future bookings."
    )
    tlrm_rented_units = fields.Integer(
        string="Rented Units", 
        compute="_compute_tlrm_counts", 
        store=False,
        help="Units currently in ongoing bookings."
    )
    tlrm_available_units = fields.Integer(
        string="Available Units", 
        compute="_compute_tlrm_counts", 
        store=False
    )
    tlrm_booked_units = fields.Integer(
        string="Booked Units",
        compute="_compute_tlrm_counts",
        store=False,
        help="Units locked for pickup (hard commitment)."
    )
    
    tlrm_status = fields.Selection([
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('rented', 'Rented'),
        ('unavailable', 'Unavailable'),
    ], string="Rental Status", compute="_compute_tlrm_status", store=False)

    @api.depends('tlrm_available_units', 'tlrm_reserved_units', 'tlrm_rented_units')
    def _compute_tlrm_status(self):
        for product in self:
            if product.tlrm_rented_units > 0:
                product.tlrm_status = 'rented'
            elif product.tlrm_reserved_units > 0:
                product.tlrm_status = 'reserved'
            elif product.tlrm_available_units <= 0:
                product.tlrm_status = 'unavailable'
            else:
                product.tlrm_status = 'available'

    def _compute_tlrm_counts(self):
        """Compute rental availability counts using fleet capacity.
        
        Uses read_group for efficient batch querying instead of multiple searches.
        
        - Reserved: Units in 'reserved' state (soft hold, doesn't block availability)
        - Booked: Units in 'booked' state (hard lock, blocks availability)
        - Rented: Units in 'ongoing' or 'finished' state (physically out)
        - Available: Fleet capacity minus booked and rented units
        """
        # Initialize all products with zero values
        for product in self:
            product.tlrm_reserved_units = 0
            product.tlrm_booked_units = 0
            product.tlrm_rented_units = 0
            product.tlrm_available_units = 0
        
        if not self:
            return
        
        # Collect all variant IDs for batch query
        all_variant_ids = self.mapped('product_variant_ids').ids
        if not all_variant_ids:
            return
        
        BookingLine = self.env['tl.rental.booking.line']
        company_id = self.env.company.id
        
        # Single read_group query for all states
        domain = [
            ('product_id', 'in', all_variant_ids),
            ('state', 'in', ['reserved', 'booked', 'ongoing', 'finished']),
            ('company_id', '=', company_id),
        ]
        groups = BookingLine._read_group(
            domain,
            groupby=['product_id', 'state'],
            aggregates=['quantity:sum'],
        )
        
        # Build lookup: product_id -> state -> quantity
        qty_by_product_state = {}
        for product_id, state, qty_sum in groups:
            pid = product_id.id if product_id else False
            if pid not in qty_by_product_state:
                qty_by_product_state[pid] = {}
            qty_by_product_state[pid][state] = qty_sum or 0.0
        
        # Assign values to each product template
        for product in self:
            reserved = 0.0
            booked = 0.0
            rented = 0.0
            
            for variant in product.product_variant_ids:
                state_qtys = qty_by_product_state.get(variant.id, {})
                reserved += state_qtys.get('reserved', 0.0)
                booked += state_qtys.get('booked', 0.0)
                rented += state_qtys.get('ongoing', 0.0) + state_qtys.get('finished', 0.0)
            
            fleet_capacity = product.tlrm_fleet_capacity or 0.0
            available = fleet_capacity - booked - rented
            
            product.tlrm_reserved_units = int(reserved)
            product.tlrm_booked_units = int(booked)
            product.tlrm_rented_units = int(rented)
            product.tlrm_available_units = int(max(available, 0.0))

