# -*- coding: utf-8 -*-
from openerp import models, fields, api
from .utils import choices_tuple


class PurchaseOrder(models.Model):
    _name = 'outsource.purchase.order'
    _rec_name = 'po_num'
    _description = 'Purchase Order'
    _order = 'po_date desc, po_num'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    # CHOICES
    # ----------------------------------------------------------
    STATES = choices_tuple(['active', 'closed'], is_sorted=False)

    # BASIC FIELDS
    # ----------------------------------------------------------
    state = fields.Selection(STATES, default='active')

    # BASIC FIELDS
    # ----------------------------------------------------------
    po_num = fields.Char(string='Purchase Order')
    po_date = fields.Date(string='Starting Date')
    po_value = fields.Float(string='PO Value', digits=(32, 2), default=0.00)
    contractor = fields.Char(string='Contractor')
    capex_commitment_value = fields.Float(string='CAPEX Commitment', digits=(32, 2), default=0.00)
    capex_expenditure_value = fields.Float(string='CAPEX Expenditure', digits=(32, 2), default=0.00)
    opex_value = fields.Float(string='OPEX Value', digits=(32, 2), default=0.00)
    revenue_value = fields.Float(string='Revenue Value', digits=(32, 2), default=0.00)
    task_num = fields.Char(string='Task Number')
    status = fields.Char(string='Status')
    remarks = fields.Text()
    type = fields.Char(string='Type')

    # MISC FIELDS
    # ----------------------------------------------------------
    renewed_date = fields.Date(string='Renewal Date')

    # RELATIONSHIPS
    # ----------------------------------------------------------
    approval_ids = fields.One2many('outsource.approval', 'po_id', string="Approvals")
    po_line_ids = fields.One2many('outsource.purchase.order.line', 'po_id', string="Purchase Order Lines")
    po_collection_id = fields.Many2one('outsource.purchase.order.collection', string='{PO Collection')

    # self reference, one new po to many renewals
    renewed_po_ids = fields.One2many('outsource.purchase.order', 'new_po_id', string="Renewals")
    new_po_id = fields.Many2one('outsource.purchase.order', string='New PO After Renewal')

    # COMPUTE FIELDS
    # ----------------------------------------------------------

    total_approval = fields.Integer(compute='_compute_total_approval', store=True)
    total_po_line = fields.Integer(compute='_compute_total_po_line', store=True)
    total_po_line_detail = fields.Integer(compute='_compute_total_po_line_detail', store=True)
    total_invoice = fields.Integer(compute='_compute_total_invoice', store=True)
    total_resource = fields.Integer(compute='_compute_total_resource', store=True)
    total_non_mobilize = fields.Integer(compute='_compute_total_non_mobilize', store=True)

    is_renewed = fields.Boolean(compute='_compute_is_renewed', store=True)

    all_po_line_detail_ids = fields.One2many('outsource.purchase.order.line.detail',
                                             'po_line_id',
                                             compute="_compute_o2m_all_po_line_detail_ids",
                                             store=True
                                             )

    @api.depends('total_approval', 'approval_ids')
    def _compute_total_approval(self):
        self.total_approval = len(self.approval_ids)

    @api.depends('total_po_line', 'po_line_ids')
    def _compute_total_po_line(self):
        self.total_po_line = len(self.po_line_ids)

    @api.depends('total_invoice', 'po_line_ids')
    def _compute_total_invoice(self):
        self.total_invoice = 0

    @api.depends('total_resource', 'po_line_ids')
    def _compute_total_resource(self):
        resource_count = 0
        for line_detail in self.mapped('po_line_ids.po_line_detail_ids'):
            if len(line_detail.resource_ids):
                resource_count += 1
            self.total_resource = resource_count

    @api.depends('total_non_mobilize', 'po_line_ids')
    def _compute_total_non_mobilize(self):
        self.total_non_mobilize = self.total_po_line_detail - self.total_resource

    @api.depends('total_po_line_detail', 'po_line_ids')
    def _compute_total_po_line_detail(self):
        self.total_po_line_detail = len(self.mapped('po_line_ids.po_line_detail_ids'))

    @api.depends('all_po_line_detail_ids', 'po_line_ids')
    def _compute_o2m_all_po_line_detail_ids(self):
        self.all_po_line_detail_ids = self.mapped('po_line_ids.po_line_detail_ids')

    # MISC FUNCTION
    # ----------------------------------------------------------
    def _compute_is_renewed(self):
        # CHECKS IF THE PO IS RENEWED BY LOOKING IF NEW PO EXIST
        self.is_renewed = bool(self.new_po_id)

    # BUTTON ACTIONS / TRANSITIONS
    # ----------------------------------------------------------
    @api.one
    def set2close(self):
        import ipdb; ipdb.set_trace()

class PurchaseOrderLine(models.Model):
    _name = 'outsource.purchase.order.line'
    _rec_name = 'po_id'

    line_num = fields.Char(string='Line Number')
    line_duration = fields.Integer(string='Duration', default=0)
    line_value = fields.Float(string='Value', digits=(32, 2), default=0.00)
    line_revise_rate = fields.Float(string='Revise Rate Value', digits=(32, 2), default=0.00)
    line_rate = fields.Float(string='Rate', digits=(32, 2), default=0.00)
    line_status = fields.Char(string='Status')
    line_actuals = fields.Float(string='Actual Value', digits=(32, 2), default=0.00)
    capex_percent = fields.Float(string='Capex %', digits=(32, 2), default=0.00)
    opex_percent = fields.Float(string='Opex %', digits=(32, 2), default=0.00)
    revenue_percent = fields.Float(string='Revenue %', digits=(32, 2), default=0.00)

    # RELATIONSHIPS
    # ----------------------------------------------------------
    po_id = fields.Many2one('outsource.purchase.order', string='Purchase Order')
    po_line_detail_ids = fields.One2many('outsource.purchase.order.line.detail',
                                  'po_line_id',
                                  string="Line Details")


class PurchaseOrderLineDetail(models.Model):
    _name = 'outsource.purchase.order.line.detail'
    _rec_name = 'job_id'

    # BASIC FIELDS
    # ----------------------------------------------------------
    job_id = fields.Char(string='Job ID')
    position = fields.Char(string='Position')
    level = fields.Char(string='Level')
    rate = fields.Float(string='Rate', digits=(32, 2), default=0.00)
    revise_rate = fields.Float(string='Revise Rate', digits=(32, 2), default=0.00)
    division = fields.Char(string='Division')
    section = fields.Char(string='Section')
    sub_section = fields.Char(string='Sub Section')
    director_name = fields.Char(string='Director Name')
    frozen_status = fields.Char(string='Frozen Status')
    approval_ref_num = fields.Char(string='Approval Ref No')
    approval_reason = fields.Text()
    kpi_2016 = fields.Char(string='KPI 2016')
    capex_percent = fields.Float(string='Capex Percent', digits=(32, 2), default=0.00)
    opex_percent = fields.Float(string='Opex Percent', digits=(32, 2), default=0.00)
    revenue_percent = fields.Float(string='Revenue Percent', digits=(32, 2), default=0.00)
    rate_diff_percent = fields.Float(string='Rate Variation', digits=(32, 2), default=0.00)

    # RELATIONSHIPS
    # ----------------------------------------------------------
    po_line_id = fields.Many2one('outsource.purchase.order.line', string='Purchase Order Line')
    resource_ids = fields.One2many('outsource.resource',
                             'po_line_detail_id',
                             string="Resource")

