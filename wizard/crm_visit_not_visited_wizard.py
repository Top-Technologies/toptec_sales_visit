# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class CrmVisitNotVisitedWizard(models.TransientModel):
    _name = "crm.visit.not.visited.wizard"
    _description = "Mark Visit as Not Visited Wizard"

    visit_id = fields.Many2one("crm.visit", string="Visit", required=True)
    not_visited_reason_id = fields.Many2one(
        comodel_name="crm.visit.reason",
        string="Not-Visited Reason",
        domain=[("category", "=", "not_visited")],
        required=True,
    )
    not_visited_notes = fields.Text(string="Explanation / Notes")

    def action_confirm(self):
        self.ensure_one()
        if self.not_visited_reason_id.requires_explanation and not self.not_visited_notes:
            raise UserError(
                _("Please enter explanation notes for reason: %s") % self.not_visited_reason_id.name
            )
        self.visit_id.write({
            "visit_status": "not_visited",
            "not_visited_reason_id": self.not_visited_reason_id.id,
            "not_visited_notes": self.not_visited_notes,
            "sales_outcome": False,
        })
        self.visit_id.message_post(
            body=_("Visit marked as Not Visited. Reason: %s. Notes: %s") % (
                self.not_visited_reason_id.name,
                self.not_visited_notes or _("None"),
            )
        )
        return {"type": "ir.actions.act_window_close"}
