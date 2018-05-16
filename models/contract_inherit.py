# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Contract(models.Model):
    _inherit = 'budget.contractor.contract'

    # BASIC FIELDS
    # ----------------------------------------------------------
    is_outsource = fields.Boolean('Is Outsource', default=False)
