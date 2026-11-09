# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class CrmVisit(models.Model):
    _name = "crm.visit"
    _description = "Sales Visit"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "planned_date desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
        index=True,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Salesperson",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        index=True,
    )
    team_id = fields.Many2one(
        comodel_name="crm.team",
        string="Sales Team",
        default=lambda self: self.env.user.sale_team_id,
        tracking=True,
        index=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer",
        required=True,
        tracking=True,
        index=True,
    )
    contact_id = fields.Many2one(
        comodel_name="res.partner",
        string="Contact Person",
        domain="[('parent_id', '=', partner_id)]",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id",
        string="Currency",
        readonly=True,
    )

    # Dates and Times
    planned_date = fields.Datetime(
        string="Planned Date",
        required=True,
        default=fields.Datetime.now,
        tracking=True,
    )
    visited_date = fields.Datetime(
        string="Visited Time",
        readonly=True,
        copy=False,
        tracking=True,
    )

    # Status and Outcome
    visit_status = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("planned", "Planned"),
            ("completed", "Completed"),
            ("not_visited", "Not Visited"),
            ("cancelled", "Cancelled"),
        ],
        string="Visit Status",
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )
    sales_outcome = fields.Selection(
        selection=[
            ("sale", "Sale Made"),
            ("no_sale", "No Sale"),
        ],
        string="Sales Outcome",
        default=False,
        tracking=True,
        index=True,
    )

    # Quotations / Orders
    sale_order_ids = fields.One2many(
        comodel_name="sale.order",
        inverse_name="visit_id",
        string="Quotations & Orders",
    )
    sale_order_count = fields.Integer(
        string="Orders Count",
        compute="_compute_sale_order_count",
    )
    total_sales_amount = fields.Monetary(
        string="Total Sales (Birr)",
        currency_field="currency_id",
        compute="_compute_sales_breakdown",
        store=True,
    )
    cash_sale_count = fields.Integer(
        string="Cash Sales",
        compute="_compute_sales_breakdown",
        store=True,
    )
    credit_sale_count = fields.Integer(
        string="Credit Sales",
        compute="_compute_sales_breakdown",
        store=True,
    )
    total_sales_count = fields.Integer(
        string="Total Sales",
        compute="_compute_sales_breakdown",
        store=True,
    )
    sale_type = fields.Selection(
        selection=[
            ("cash", "Cash"),
            ("credit", "Credit"),
            ("both", "Cash & Credit"),
        ],
        string="Sale Type",
        compute="_compute_sales_breakdown",
        store=True,
        index=True,
    )
    cash_sale_amount = fields.Monetary(
        string="Cash Sales (Birr)",
        currency_field="currency_id",
        compute="_compute_sales_breakdown",
        store=True,
    )
    credit_sale_amount = fields.Monetary(
        string="Credit Sales (Birr)",
        currency_field="currency_id",
        compute="_compute_sales_breakdown",
        store=True,
    )
    no_sale_count = fields.Integer(
        string="No Sales",
        compute="_compute_sales_breakdown",
        store=True,
    )
    total_visit_count = fields.Integer(
        string="Total Visits (Cash + Credit + No Sales)",
        compute="_compute_sales_breakdown",
        store=True,
    )

    # No Sale / Not Visited reasons
    no_sale_reason_id = fields.Many2one(
        comodel_name="crm.visit.reason",
        string="No-Sale Reason",
        domain=[("category", "=", "no_sale")],
        tracking=True,
    )
    no_sale_notes = fields.Text(string="Customer Feedback / Reason Details")

    not_visited_reason_id = fields.Many2one(
        comodel_name="crm.visit.reason",
        string="Not-Visited Reason",
        domain=[("category", "=", "not_visited")],
        tracking=True,
    )
    not_visited_notes = fields.Text(string="Not-Visited Explanation")

    # -------------------------------------------------------------------------
    # Computes & Constraints
    # -------------------------------------------------------------------------
    @api.depends("sale_order_ids")
    def _compute_sale_order_count(self):
        for visit in self:
            visit.sale_order_count = len(visit.sale_order_ids)

    @api.depends("sales_outcome", "sale_order_ids.state", "sale_order_ids.sale_type", "sale_order_ids.amount_total")
    def _compute_sales_breakdown(self):
        for visit in self:
            visit.no_sale_count = 1 if visit.sales_outcome == "no_sale" else 0
            visit.total_visit_count = visit.cash_sale_count + visit.credit_sale_count + visit.no_sale_count
            valid_orders = visit.sale_order_ids.filtered(lambda o: o.state != "cancel")
            cash_orders = valid_orders.filtered(lambda o: o.sale_type == "cash")
            credit_orders = valid_orders.filtered(lambda o: o.sale_type == "credit")
            visit.cash_sale_count = len(cash_orders)
            visit.credit_sale_count = len(credit_orders)
            visit.total_sales_count = visit.cash_sale_count + visit.credit_sale_count
            visit.cash_sale_amount = sum(cash_orders.mapped("amount_total"))
            visit.credit_sale_amount = sum(credit_orders.mapped("amount_total"))
            visit.total_sales_amount = sum(valid_orders.mapped("amount_total"))

            if visit.sales_outcome == "sale":
                if credit_orders and not cash_orders:
                    visit.sale_type = "credit"
                elif cash_orders and not credit_orders:
                    visit.sale_type = "cash"
                elif cash_orders and credit_orders:
                    visit.sale_type = "both"
                else:
                    visit.sale_type = False
            else:
                visit.sale_type = False

    @api.constrains("sales_outcome", "visit_status", "no_sale_reason_id")
    def _check_outcome_rules(self):
        for visit in self:
            if visit.visit_status == "not_visited" and visit.sales_outcome == "sale":
                raise ValidationError(_("A visit marked 'Not Visited' cannot have a 'Sale Made' outcome."))
            if visit.visit_status == "completed":
                if not visit.sales_outcome:
                    raise ValidationError(_("Please specify a Sales Outcome (Sale Made or No Sale) to complete the visit."))
                if visit.sales_outcome == "no_sale":
                    if not visit.no_sale_reason_id:
                        raise ValidationError(_("A No-Sale reason is required when the visit outcome is 'No Sale'."))
                    if visit.no_sale_reason_id.requires_explanation and not visit.no_sale_notes:
                        raise ValidationError(_("Written feedback/notes are required for reason '%s'.") % visit.no_sale_reason_id.name)

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("crm.visit") or _("New")
        return super().create(vals_list)

    # -------------------------------------------------------------------------
    # Actions & Workflow
    # -------------------------------------------------------------------------
    def action_plan(self):
        for visit in self:
            if visit.visit_status not in ("draft", "cancelled"):
                raise UserError(_("Only Draft or Cancelled visits can be moved to Planned."))
            visit.write({"visit_status": "planned"})

    def action_mark_visited(self):
        """Store the current time and mark the visit as completed."""
        for visit in self:
            if visit.visited_date:
                raise UserError(_("This visit has already been marked as visited."))
            if not visit.sales_outcome:
                raise UserError(_("Please select an Outcome (Sale Made or No Sale) before marking the visit as visited."))
            now = fields.Datetime.now()
            visit.write({
                "visited_date": now,
                "visit_status": "completed",
            })
            visit.message_post(
                body=_("Visit marked as Visited at %(time)s.", time=fields.Datetime.to_string(now))
            )

    def action_mark_not_visited(self):
        for visit in self:
            if not visit.not_visited_reason_id or (
                visit.not_visited_reason_id.requires_explanation and not visit.not_visited_notes
            ):
                return {
                    "name": _("Mark as Not Visited"),
                    "type": "ir.actions.act_window",
                    "res_model": "crm.visit.not.visited.wizard",
                    "view_mode": "form",
                    "target": "new",
                    "context": {
                        "default_visit_id": visit.id,
                        "default_not_visited_reason_id": visit.not_visited_reason_id.id,
                        "default_not_visited_notes": visit.not_visited_notes,
                    },
                }
            visit.write({
                "visit_status": "not_visited",
                "sales_outcome": False,
            })
            visit.message_post(
                body=_("Visit marked as Not Visited. Reason: %s. Notes: %s") % (
                    visit.not_visited_reason_id.name,
                    visit.not_visited_notes or _("None"),
                )
            )

    def action_cancel(self):
        for visit in self:
            visit.write({"visit_status": "cancelled"})

    def action_reset_to_draft(self):
        for visit in self:
            visit.write({
                "visit_status": "draft",
                "sales_outcome": False,
            })

    def action_create_quotation(self):
        """Create a new standard quotation linked to this visit."""
        self.ensure_one()
        order_vals = {
            "partner_id": self.partner_id.id,
            "user_id": self.user_id.id,
            "team_id": self.team_id.id if self.team_id else False,
            "company_id": self.company_id.id,
            "visit_id": self.id,
            "origin": self.name,
        }
        order = self.env["sale.order"].create(order_vals)
        now = fields.Datetime.now()
        self.write({
            "sales_outcome": "sale",
            "visit_status": "completed",
            "visited_date": self.visited_date or now,
        })
        self.message_post(
            body=_("Quotation %(order)s created from this visit. Visit marked as Visited at %(time)s.",
                   order=order.name, time=fields.Datetime.to_string(now))
        )

        return {
            "name": _("Quotation"),
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "res_id": order.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_quotations(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("sale.action_quotations_with_onboarding")
        action["domain"] = [("visit_id", "=", self.id)]
        action["context"] = {
            "default_partner_id": self.partner_id.id,
            "default_user_id": self.user_id.id,
            "default_team_id": self.team_id.id if self.team_id else False,
            "default_company_id": self.company_id.id,
            "default_visit_id": self.id,
        }
        return action
