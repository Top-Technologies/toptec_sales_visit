# -*- coding: utf-8 -*-
from odoo import fields, models

class CrmVisitReason(models.Model):
    _name = "crm.visit.reason"
    _description = "Sales Visit Reason"
    _order = "sequence, id"

    name = fields.Char(string="Reason", required=True, translate=True)
    sequence = fields.Integer(string="Sequence", default=10)
    category = fields.Selection(
        selection=[
            ("no_sale", "No Sale"),
            ("not_visited", "Not Visited"),
        ],
        string="Category",
        required=True,
        default="no_sale",
        index=True,
    )
    requires_explanation = fields.Boolean(
        string="Requires Explanation",
        help="If checked, the salesperson or manager must enter written notes explaining this reason.",
        default=False,
    )
    active = fields.Boolean(default=True)
