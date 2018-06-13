# -*- coding: utf-8 -*-

from odoo import models, fields


class UnitRate(models.Model):
    _name = 'budget.outsource.unit.rate'
    _rec_name = 'position_name'
    _description = 'Unit Rate'

    position_name = fields.Char()
    position_level = fields.Char()
    amount = fields.Monetary(string='Amount', currency_field='currency_id')

    # RELATIONSHIPS
    # ----------------------------------------------------------
    currency_id = fields.Many2one('res.currency', readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id)

    contractor_id = fields.Many2one('budget.contractor.contractor', string='Contractor')
    contract_id = fields.Many2one('budget.contractor.contract', string='Contract')
