<<<<<<< HEAD
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
=======
TL Rental Manager
=================

Overview
--------

TL Rental Manager adds rental management on top of stockable products and
projects. It lets you:

- Plan and track product rentals by period.
- Link rentals to projects or tasks.
- Check availability with a week‑based capacity grid.
- Keep stock and reservations consistent during the rental lifecycle.

Use Cases
---------

- Rent out physical equipment (tools, machines, vehicles).
- Plan project‑specific rentals and see if stock is sufficient.
- Get a quick overview of booked vs available units per week.

Main Features
-------------

- Rental bookings with lines, periods and states (draft, reserved, ongoing, finished).
- Automatic booking sequence and scheduled job to update states.
- Availability grid per product and week, based on `stock.quant` and existing bookings.
- Calendar integration with week numbers tuned for Swedish conventions.
- Multi‑company aware domains and record rules.
- Dedicated security groups for rental users and managers.

Configuration
-------------

1. Install the module *TL Rental Manager*.
2. Assign security groups:

   - **Rental User** (basic usage).
   - **Rental Manager** (full CRUD, configuration).

3. (Optional) Adjust the scheduled action:

   - *Settings → Technical → Automation → Scheduled Actions*
   - **Stock Rental Booking: Update States**

Usage
-----

- Go to **Inventory / Rentals** (or your configured menu entry).
- Create a **Rental Booking**:
  
  - Select customer, company and rental period.
  - Add **Rental Booking Lines** with products and quantities.
  - Confirm to reserve stock.

- Open the **Rental Availability** action to:

  - See weekly capacity per product.
  - Check booked vs available units.
  - Drill down to the product form from the grid.

Security
--------

- Access rights are defined per model and group in
  `[security/ir.model.access.csv](cci:7://file:///c:/odoo_custom_addons/tl-rental-manager/security/ir.model.access.csv:0:0-0:0)`.
- Multi‑company access is enforced via record rules in
  `[security/rental_security.xml](cci:7://file:///c:/odoo_custom_addons/tl-rental-manager/security/rental_security.xml:0:0-0:0)`.
- Sequences are protected with ``noupdate="1"`` to avoid changes on upgrade.

Technical Details
-----------------

- Models:

  - ``stock.rental.booking``
  - ``stock.rental.booking.line``

- Key technical components:

  - Availability computation in
    `[stock.rental.booking.line.get_availability_grid](cci:1://file:///c:/odoo_custom_addons/stock_rental_manager/models/rental_booking.py:337:4-556:21)`.
  - OWL front‑end action and template for the availability grid:

    - JS: `[static/src/js/rental_availability_action.js](cci:7://file:///c:/odoo_custom_addons/tl-rental-manager/static/src/js/rental_availability_action.js:0:0-0:0)`
    - XML: `[static/src/xml/rental_availability_templates.xml](cci:7://file:///c:/odoo_custom_addons/tl-rental-manager/static/src/xml/rental_availability_templates.xml:0:0-0:0)`

  - Controller endpoints for JSON availability:

    - ``/stock_rental/availability_grid/global``
    - ``/stock_rental/availability_grid/booking``

Dependencies
------------

- Odoo 19.0 Community
- Core modules: ``base``, ``product``, ``stock``, ``project``, ``mail``

License
-------

This module is licensed under the LGPL‑3 license.
>>>>>>> 6b9fd7d2f69a3a04742cd17a95474083b250e6bf
