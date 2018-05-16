# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Invoice(models.Model):
    _inherit = 'budget.invoice.invoice'

    # BASIC FIELDS
    # ----------------------------------------------------------
    # TODO DEPRECATED
    is_outsource = fields.Boolean('Is Outsource', default=False)

    is_outsource = fields.Boolean('Is Outsource', default=False)

    # outsource_actual_hour = fields.Float(default=0.00)
    # outsource_claim_hour = fields.Float(default=0.00)

    # RELATIONSHIPS
    # ----------------------------------------------------------
    # mobilize_id = fields.Many2one('budget.outsource.mobilize')
    # position_id = fields.Many2one('budget.outsource.position')

    # REDIRECT/OPEN OTHER VIEWS BUTTONS
    # ----------------------------------------------------------
    def summary_wizard(self):
        res = super(Invoice, self).summary_wizard()
        res['context']['default_is_outsource'] = self.is_outsource
        return res
