from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    tlrm_booking_id = fields.Many2one('tl.rental.booking', string="Rental Booking")
    tlrm_direction = fields.Selection([
        ('out', 'Rental Out'),
        ('in', 'Rental In'),
    ], string="Rental Direction")

    def action_done(self):
        res = super().action_done()
        for picking in self:
            booking = picking.tlrm_booking_id
            if not booking:
                continue
            if picking.tlrm_direction == 'out' and booking.state == 'reserved':
                booking.state = 'ongoing'
            elif picking.tlrm_direction == 'in':
                if booking.state in ['ongoing', 'finished']:
                    booking.state = 'returned'
        return res
