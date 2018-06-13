from odoo import models, fields, api


class Spoc(models.Model):
    _inherit = 'budget.enduser.spoc'

    # BASIC FIELDS
    # ----------------------------------------------------------

    # RELATIONSHIPS
    # ----------------------------------------------------------

    # ONCHANGE FIELDS
    # ----------------------------------------------------------

    # MORPH
    # ----------------------------------------------------------
    @api.model
    def create(self, vals):
        spoc = super(Spoc, self).create(vals)
        spoc.groups_id |= self.env.ref('budget_outsource.group_outsource_enduser')
        return spoc
