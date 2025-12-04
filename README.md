# TL Rental Manager

Odoo 19 Community module for managing stockable product rentals with project-based bookings and availability planning.

## Features

- **Rental Bookings**: Create and manage rental bookings linked to projects
- **Availability Grid**: Visual week-by-week availability calendar for all products
- **Stock Integration**: Automatic stock moves when confirming/returning rentals
- **Multi-company Support**: Full multi-company record rules

## Module Structure

```
tl_rental_manager/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── controllers.py          # JSON-RPC endpoints for availability API
├── data/
│   ├── rental_cron.xml         # Scheduled actions
│   └── rental_sequence.xml     # Booking reference sequence (TLRM/xxxxx)
├── models/
│   ├── __init__.py
│   ├── product.py              # product.template extensions (tlrm_* fields)
│   ├── rental_booking.py       # tl.rental.booking & tl.rental.booking.line
│   └── stock_picking.py        # stock.picking extensions (tlrm_* fields)
├── security/
│   ├── ir.model.access.csv     # Access rights
│   └── rental_security.xml     # Groups and record rules
├── static/
│   └── src/
│       ├── css/
│       │   └── rental_availability.css   # Availability grid styles
│       ├── js/
│       │   ├── rental_availability_action.js  # OWL client action
│       │   └── rental_calendar.js             # Calendar view patch
│       └── xml/
│           └── rental_availability_templates.xml  # OWL templates
└── views/
    ├── product_view.xml              # Product form extensions
    └── rental_booking_views.xml      # Booking views, menus, actions
```

## Naming Conventions

This module follows Odoo 19 community guidelines with unique prefixes to avoid conflicts:

| Type | Prefix | Example |
|------|--------|---------|
| Models | `tl.rental.*` | `tl.rental.booking`, `tl.rental.booking.line` |
| Fields on inherited models | `tlrm_` | `tlrm_price_hour`, `tlrm_status`, `tlrm_booking_id` |
| XML IDs | `tlrm_` | `tlrm_action_booking`, `tlrm_view_booking_form` |
| Security groups | `tlrm_group_` | `tlrm_group_user`, `tlrm_group_manager` |
| CSS classes | `o_tlrm_` | `o_tlrm_availability_action`, `o_tlrm_cell_clickable` |
| Client action tags | `tlrm_` | `tlrm_availability_global` |
| Sequence prefix | `TLRM/` | `TLRM/00001` |

## Security Groups

- **TL Rental User** (`tlrm_group_user`): Basic rental access (read, write, create)
- **TL Rental Manager** (`tlrm_group_manager`): Full access including delete

Stock users automatically inherit TL Rental User permissions.

## Models

### tl.rental.booking
Main booking header with:
- Project reference (required)
- Source/Rental warehouse
- Date range (start/end)
- State workflow: draft → reserved → ongoing → finished → returned

### tl.rental.booking.line
Booking lines with:
- Product and quantity
- Warehouse overrides per line
- Related fields from booking (dates, state, project)

## Availability Grid

The availability grid (`Inventory → Rental → Availability`) provides:
- Week-by-week view of product availability
- Color-coded cells (green=free, yellow=partial, red=full)
- Click-to-drill-down on booked cells
- Search and sort functionality
- Week navigation (Previous/Today/Next)

## Dependencies

- `base`
- `product`
- `stock`
- `project`
- `mail`

## Installation

1. Place module in your Odoo addons path
2. Update apps list: `Settings → Apps → Update Apps List`
3. Install: Search for "TL Rental Manager" and click Install

## License

LGPL-3
