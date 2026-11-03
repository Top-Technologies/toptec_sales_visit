# -*- coding: utf-8 -*-
from odoo import fields, models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    visit_id = fields.Many2one(
        comodel_name="crm.visit",
        string="Originating Visit",
        copy=False,
        index=True,
        help="Field visit during which this quotation or sales order was generated.",
    )
    sale_type = fields.Selection(
        selection=[
            ("cash", "Cash"),
            ("credit", "Credit"),
        ],
        string="Sale Type",
        default="cash",
        required=True,
        tracking=True,
        index=True,
        help="Classification of sale (Cash or Credit). Used for visit sales reporting.",
    )
