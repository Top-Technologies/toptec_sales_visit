# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = "res.partner"

    visit_ids = fields.One2many(
        comodel_name="crm.visit",
        inverse_name="partner_id",
        string="Visits",
    )
    visit_count = fields.Integer(
        string="Visit Count",
        compute="_compute_visit_count",
    )

    @api.depends("visit_ids")
    def _compute_visit_count(self):
        for partner in self:
            partner.visit_count = len(partner.visit_ids)

    def action_view_visits(self):
        self.ensure_one()
        return {
            "name": _("Visits"),
            "type": "ir.actions.act_window",
            "res_model": "crm.visit",
            "view_mode": "list,kanban,calendar,form",
            "domain": [("partner_id", "=", self.id)],
            "context": {"default_partner_id": self.id},
        }
