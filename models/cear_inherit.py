# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Cear(models.Model):
    _inherit = 'budget.capex.cear'

    # BASIC FIELDS
    # ----------------------------------------------------------
    # TODO DEPRECATED
    is_resource = fields.Boolean('Is Resource', default=False)

    is_outsource = fields.Boolean('Is Resource', default=False)
