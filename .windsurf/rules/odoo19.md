---
trigger: always_on
---

Odoo 19 Addon Development Rulebook

Target version: Odoo 19 (strict)
Odoo 18 is referenced only to identify legacy patterns that must NOT be used in new code.

1. Module Structure Rules (Odoo 19 Strict)
1.1 Always use the modern addon structure
your_module/
    __init__.py
    __manifest__.py
    models/
        __init__.py
        ...
    views/
        ...
    security/
        ir.model.access.csv
    data/
        ...
    static/
        src/
            js/
            xml/
            scss/

1.2 Manifest must be a Python dict (no JSON)

Keys must be valid for Odoo 19:

name, summary, version, depends, data, assets, license, installable, etc.

No deprecated manifest keys from older versions.

1.3 Asset loading uses ONLY the assets key in the manifest

Correct Odoo 19 style:

"assets": {
    "web.assets_backend": [
        "module_name/static/src/js/my_script.js",
    ],
}

1.4 Asset XML files (views/assets.xml) are optional

Use them only if you define QWeb templates.
Never use them to inject JS/CSS in Odoo 19.
(That’s manifest-only now.)

2. View Development Rules (Odoo 19 Strict)
2.1 The only valid list view root tag is <list>

Tree views are removed.
Odoo 19 rejects any <tree> usage.

Correct Odoo 19 list view:

<list string="My Items">
    <field name="name"/>
    <field name="date"/>
</list>

If you see:
<tree> ... </tree>


→ This is Odoo 17/older code.
→ Will crash Odoo 19 (“Invalid view type: 'tree'”).

2.2 Inherited list views must also use <list>

Example:

<list position="inside">
    <field name="x_note"/>
</list>

2.3 Valid view types in Odoo 19

list

form

kanban

calendar

gantt

pivot

graph

activity

search

qweb

Anything else is invalid.

2.4 XML must wrap content in <odoo>

Example:

<odoo>
  <record id="..." model="ir.ui.view">
      ...
  </record>
</odoo>

3. ORM, Models, and Python Rules (Odoo 19 Strict)
3.1 NEVER use deprecated attributes / legacy API

Forbidden in Odoo 19 (but existed in earlier versions):

odoo.osv

self._cr

self._uid

self._context

Correct Odoo 19 instead:
self.env.cr
self.env.uid
self.env.context

3.2 Model declaration format (mandatory)
from odoo import models, fields, api

class MyModel(models.Model):
    _name = "my.model"
    _description = "My Model"

    name = fields.Char()

3.3 Domain logic

Odoo 19 supports dynamic date domains.
Examples that are valid in 19:

domain=[("date", ">", fields.Date.today())]


Odoo 18 lacked some of the new dynamic syntax.

3.4 Avoid direct SQL unless necessary

Use:

self.env.cr.execute(...)


Never self._cr.execute(...).

4. Cron Jobs / ir.cron Rules (Odoo 19 Strict)

Odoo 19 removes several fields that existed long ago.

Forbidden in Odoo 19:

numbercall

doall

If your addon contains these, installation will crash.

Valid Odoo 19 cron definition:
<odoo>
  <record id="my_cron" model="ir.cron">
    <field name="name">My Cron</field>
    <field name="active" eval="True"/>
    <field name="model_id" ref="model_my_model"/>
    <field name="state">code</field>
    <field name="code">model._run_cron()</field>
    <field name="interval_number">10</field>
    <field name="interval_type">minutes</field>
    <field name="user_id" ref="base.user_root"/>
  </record>
</odoo>

If you need limited-run jobs:

Implement counters in Python.
You cannot rely on numbercall anymore.

5. JavaScript / Webclient Rules (Odoo 19 Strict)
5.1 Odoo 19 uses OWL

The LLM must generate or reason in terms of OWL components.

Examples:

Component classes

useState(), useEffect(), useService()

async event handlers

Correct import paths: "@web/..."

5.2 No legacy QWeb-based JS widgets

Old-style JS widgets (pre-OWL) should never be generated unless explicitly requested.

5.3 Assets loaded in manifest only

(Repeating for emphasis.)

6. Security / Access Rules (Odoo 19 Strict)
6.1 ir.model.access.csv format stays the same
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink

6.2 Record rules still work normally

Use:

<record id="rule_example" model="ir.rule">
    <field name="name">Example Rule</field>
    <field name="model_id" ref="model_my_model"/>
    <field name="domain_force">[("user_id","=",uid)]</field>
</record>

6.3 Odoo 19 improves access UI

No impact on module code but helpful to remember while debugging.

7. Major Odoo 19-Specific Functional Changes (Developer Impact Only)
7.1 Pivot tables support GROUPING SETS (19 only)

If generating or debugging analytical views in 19, this is allowed.

7.2 Activities app is improved in 19

Activity-related automation or custom views may behave differently compared to 18.

7.3 Website/eCommerce uses more OWL

Templates and JS behavior changed.
LLM must generate OWL-style website customizations.

7.4 Inventory: Odoo 19 supports multi-level packages

If coding stock logic, multi-level packages may appear or must be supported.

8. Debugging Rules (Extremely Important)
8.1 If a view crashes with “Invalid view type”

Your view uses <tree> or wrong tags → Replace with <list>.

8.2 If cron creation fails with "Invalid field ‘numbercall’"

You used obsolete fields → Remove them.

8.3 If Odoo complains “Unknown comodel_name”

→ Missing dependency in depends.
Example:
If code references "sale.order" you MUST add "sale" or "sale_management".

8.4 If a module does not appear in the Apps list:

Checklist:

Folder structure correct

Manifest valid Python

Addons path correct

Restart Odoo service

Remove Apps filter

Look at logs for parse errors

8.5 If JS changes do not load

You forgot the manifest assets section

Or browser cache → hard refresh

Or JS syntax error in OWL component

8.6 If XML fails to load with a line/column error

Most common mistakes:

Missing <odoo> wrapper

Forgotten closing tag

Wrong view tag (<tree> instead of <list>)

9. Migration Rule (18 → 19) for Addons

The LLM must base all reasoning on these core differences:

Required changes:

Replace all <tree> → <list>

Remove cron fields numbercall, doall

Replace deprecated _cr, _uid, _context

Convert QWeb JS widgets → OWL components

Update assets to use manifest-based loading

Check for new constraints in pivot, activities, website

Optional:

Add 19-specific features (AI, grouping sets, multi-level packaging)

10. Direct If/Then Rules for the LLM (Version Enforcement)
10.1 Version enforcement

IF user does not specify a version
→ Use Odoo 19 only.

10.2 View rendering

IF generating any list view
→ Must use <list>.

10.3 Scheduled actions

IF generating cron XML
→ Must not generate numbercall or doall.

10.4 ORM access

IF accessing cursor/user/context
→ Must use self.env.* not deprecated variants.

10.5 JS components

IF generating frontend/backend JS
→ Must use OWL syntax.

10.6 Debug explanations

IF an error resembles patterns from older Odoo (like “Unknown view type 'tree'”)
→ Identify it as a legacy-pattern error and correct to Odoo 19 standard.



Notes in swedish:
# Odoo 19 – Tekniska noter och nya regler

## 1. `read_group` är deprecated

- Sedan Odoo 19.0 finns en varning:
  - `DeprecationWarning: Since 19.0, read_group is deprecated. Please use _read_group in the backend code or formatted_read_group for a complete formatted result`.
- Konsekvens för egen kod:
  - Befintligt `read_group` fungerar fortfarande men ger varningar i loggen.
  - Ny kod bör skriva om till `_read_group` eller `formatted_read_group` när möjligt.

## 2. Postgres-versionkrav

- Loggar visar:
  - `UserWarning: Postgres version is 120004, lower than minimum required 130000`.
- Odoo 19 förväntar sig minst PostgreSQL 13.
- Lägre versioner fungerar, men ger varningar och är inte officiellt supportade.

## 3. `read_group` resultatstruktur

- I Odoo 19 (och senare 14+) returnerar `read_group` fält med **ursprungligt fältnamn** även när man anger `':sum'` i argumentet.
  - Exempel-anrop:
    - `Quant.read_group(domain, ['quantity:sum', 'reserved_quantity:sum'], [])`
  - Exempel-resultat (utdrag från loggar):
    - `{'__count': 1, 'quantity': 10.0, 'reserved_quantity': 0.0, '__domain': [...]}`
- Viktigt:
  - Nycklarna är `quantity` och `reserved_quantity`, **inte** `quantity_sum` eller `reserved_quantity_sum`.
  - Felaktig användning av `quantity_sum` ger alltid 0 (eller `None`) och leder till att beräkningar som lagerkapacitet blir 0 trots att det finns lager.

## 4. Global lagerkapacitet per bolag

- I den här modulen beräknas tillgänglighet för uthyrning globalt per bolag:
  - Domän mot `stock.quant`:
    - `('product_id', '=', product.id)`
    - `('company_id', '=', company.id)`
    - `('location_id.usage', '=', 'internal')`
- Detta innebär:
  - Tillgänglig kapacitet bygger på **allt internt lager** inom bolaget, oberoende av specifikt warehouse.
  - Detta kan skilja sig från standard Odoo-logik om man normalt filtrerar per warehouse/location.

## 5. Skillnad mellan "On Hand" och uthyrningskontrollen

- `On Hand` i Odoo:
  - Visar globalt lager för produkten över alla interna locations.
- Uthyrningskontrollen i modulen:
  - Räknar också globalt (i nuvarande version), men kräver att `read_group` läses korrekt (se punkt 3).

## 6. Rekommendationer vid utveckling mot Odoo 19

- Kontrollera alltid i loggarna vilka nycklar `read_group` faktiskt returnerar.
- Var beredd på deprecations (som `read_group`) och planera migration till nya API:n (`_read_group`/`formatted_read_group`).
- Se till att Postgres-versionen på sikt uppgraderas till minst 13 för att slippa varningar och få officiellt stöd.

## 7. `stock.move` och fältet `name`

- I den här Odoo 19-byggnaden accepterar modellen `stock.move` **inte** ett fält `name` vid `create`.
- Försök att göra `Move.create({'name': ...})` ger felet:
  - `ValueError: Invalid field 'name' in 'stock.move'`.
- Rekommenderat arbetssätt:
  - Skicka bara standardfält: `product_id`, `product_uom`, `product_uom_qty`, `picking_id`, `company_id`, `location_id`, `location_dest_id`, osv.
  - Låt Odoo själv hantera visningsnamn (`display_name`) baserat på produkt och plockning.


## När du hittar nya saker under tiden vi utvecklar som skiljer de tidigare odoo-versionerna med odoo 19 som vi använder nu, lägg då till det i Odoo 19.md i root foldern. Alltså, alla buggar vi hittar eller problem vi stöter på pga deprecation, skriv in dom i .md filen så att vi kan lära oss från våra misstag i nya promptfönster.


OWL documentation:
https://github.com/odoo/owl/blob/master/doc/readme.md

🦉 Owl overview 🦉
Here is a list of everything exported by the Owl library:

Main entities:

App: represent an Owl application (mainly a root component,a set of templates, and a config)
Component: the main class to define a concrete Owl component
mount: main entry point for most application: mount a component to a target
xml: helper to define an inline template
Reactivity

useState: create a reactive object (hook, linked to a specific component)
reactive: create a reactive object (not linked to any component)
markRaw: mark an object or array so that it is ignored by the reactivity system
toRaw: given a reactive objet, return the raw (non reactive) underlying object
Lifecycle hooks:

onWillStart: hook to define asynchronous code that should be executed before component is rendered
onMounted: hook to define code that should be executed when component is mounted
onWillPatch: hook to define code that should be executed before component is patched
onWillUpdateProps: hook to define code that should be executed before component is updated
onPatched: hook to define code that should be executed when component is patched
onWillRender: hook to define code that should be executed before component is rendered
onRendered: hook to define code that should be executed after component is rendered
onWillUnmount: hook to define code that should be executed before component is unmounted
onWillDestroy: hook to define code that should be executed before component is destroyed
onError: hook to define a Owl error handler
Other hooks:

useComponent: return a reference to the current component (useful to create derived hooks)

