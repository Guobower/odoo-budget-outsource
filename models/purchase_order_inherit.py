# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'budget.purchase.order'

    # BASIC FIELDS
    # ----------------------------------------------------------
    # TODO DEPRECATED
    is_outsource = fields.Boolean('Is Outsource', default=False)

    is_outsource = fields.Boolean('Is Outsource', default=False)

    # Already Exist in base Purchase Order
    # num, date, amount

    # TODO NEED TO MAKE IT DIFFERENT BUDGETS
    budget = fields.Char(string='Budget')
    capex_commitment_value = fields.Float(string='CAPEX Commitment', digits=(32, 2), default=0.00)
    capex_expenditure_value = fields.Float(string='CAPEX Expenditure', digits=(32, 2), default=0.00)
    opex_value = fields.Float(string='OPEX Value', digits=(32, 2), default=0.00)
    revenue_value = fields.Float(string='Revenue Value', digits=(32, 2), default=0.00)
    task_num = fields.Char(string='Task Number')

    renew_status = fields.Char(string='Renew Status')
    renew_po_no = fields.Char(string='Renew PO No')
    po_status = fields.Char(string='PO Status')
    po_remarks = fields.Text(string='PO Remarks')
    po_type = fields.Char(string='PO Type')

    # RELATIONSHIPS
    # ----------------------------------------------------------
    outsource_position_ids = fields.One2many('budget.outsource.position', 'po_id', string="Outsource Positions")
    contractor_id = fields.Many2one('budget.contractor.contractor', string='Contractor')

    # COMPUTE FIELDS
    # ----------------------------------------------------------
    total_position = fields.Integer(compute='_compute_total_position',
                                    store=True)

    @api.one
    @api.depends('outsource_position_ids')
    def _compute_total_position(self):
        self.total_position = len(self.outsource_position_ids)
