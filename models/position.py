# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Position(models.Model):
    _name = 'budget.outsource.position'
    _rec_name = 'identifier'
    _description = 'Position'
    _inherit = ['mail.thread', 'budget.enduser.mixin']

    # BASIC FIELDS
    # ----------------------------------------------------------
    # TODO MAKE THIS AUTOINCREMENTING
    identifier = fields.Char()

    os_ref = fields.Char()
    name = fields.Char()
    level = fields.Char()

    capex_percent = fields.Float(default=0, digits=(12, 2))
    opex_percent = fields.Float(default=0, digits=(12, 2))
    revenue_percent = fields.Float(default=0, digits=(12, 2))

    # RELATIONSHIPS
    # ----------------------------------------------------------
    currency_id = fields.Many2one('res.currency', readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    po_id = fields.Many2one('budget.purchase.order', string='Purchase Order')

    # COMPUTE FIELDS
    # ----------------------------------------------------------
    unit_rate = fields.Monetary(currency_field='currency_id',
                                compute='_compute_unit_rate',
                                store=True)

    @api.one
    @api.depends('name', 'level', 'po_id', 'po_id.contractor_id')
    def _compute_unit_rate(self):
        if self.name and self.level and self.mapped('po_id.contractor_id'):
            unit_rate_id = self.env['budget.outsource.unit.rate'].search([
                ('position_name', '=', self.name),
                ('position_level', '=', self.level),
                ('contractor_id', '=', self.mapped('po_id.contractor_id').id)
            ])
            self.unit_rate = unit_rate_id.amount

        else:
            self.unit_rate = 0.0
