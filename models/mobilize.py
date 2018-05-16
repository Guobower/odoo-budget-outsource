# -*- coding: utf-8 -*-
from odoo import models, fields, api


# TODO ADD ATTENDANCE TABLE TO TAKE MONTHLY/PERIODIC TIMINGS
class Mobilize(models.Model):
    _name = 'budget.outsource.mobilize'
    _rec_name = 'resource_name'
    _description = 'Mobilize Resource'
    _inherit = ['mail.thread']

    STATES = [
        ('not mobilized', 'Not Mobilized'),
        ('mobilized', 'Mobilized'),
    ]
    # BASIC FIELDS
    # ----------------------------------------------------------
    is_mobilized = fields.Boolean(default=True)

    state = fields.Selection(string='Status', selection=STATES, default='not mobilized')
    revise_rate = fields.Monetary(string='Revised Rate', currency_field='currency_id', default=0.00)

    manager = fields.Char(string='Manager')
    director = fields.Char(string='Director')

    approval_ref_num = fields.Char(string='Approval Reference Number')
    approval_reason = fields.Text(string='Approval Reason')

    # RELATED FIELD
    # ----------------------------------------------------------
    position_name = fields.Char(string='Position', store=True, related='position_id.name')
    os_ref = fields.Char(string='OS Reference', store=True, related='position_id.os_ref')
    level = fields.Char(string='Position Level', store=True, related='position_id.level')
    unit_rate = fields.Monetary(string='Unit Rate', store=True, related='position_id.unit_rate',
                                currency_field='currency_id')
    capex_percent = fields.Float(string='CAPEX %', store=True, related='position_id.capex_percent')
    opex_percent = fields.Float(string='OPEX %', store=True, related='position_id.opex_percent')
    revenue_percent = fields.Float(string='Revenue %', store=True, related='position_id.revenue_percent')

    division_id = fields.Many2one(string='Division', store=True, related='position_id.division_id')
    section_id = fields.Many2one(string='Section', store=True, related='position_id.section_id')
    sub_section_id = fields.Many2one(string='Sub Section', store=True, related='position_id.sub_section_id')
    po_id = fields.Many2one(string='Purchase Order Number', store=True, related='position_id.po_id')

    resource_name = fields.Char(string='Name', store=True, related='resource_id.name')
    type = fields.Char(string='Type', store=True, related='resource_id.type')
    type_class = fields.Char(string='Type Class', store=True, related='resource_id.type_class')
    agency_ref_num = fields.Char(string='Agency Reference', store=True, related='resource_id.agency_ref_num')
    emp_num = fields.Char(string='Employee Number', store=True, related='resource_id.emp_num')
    date_of_join = fields.Date(string='Date of Joining', store=True, related='resource_id.date_of_join')
    date_of_last_working_day = fields.Date(string='Last Working Day', store=True,
                                           related='resource_id.date_of_last_working_day')
    has_tool_or_uniform = fields.Boolean(string='Has Tool/Uniform', store=True,
                                         related='resource_id.has_tool_or_uniform')

    # RELATIONSHIPS
    # ----------------------------------------------------------
    currency_id = fields.Many2one('res.currency', readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    resource_id = fields.Many2one('budget.outsource.resource', string='ResID')
    position_id = fields.Many2one('budget.outsource.position', string='PODetID')

    attendance_ids = fields.One2many('budget.outsource.mobilize.attendance',
                                     'mobilize_id',
                                     string='Attendances')

    # COMPUTE FIELDS
    # ----------------------------------------------------------
    required_hours = fields.Float(compute='_compute_required_hours')
    rendered_hours = fields.Float(compute='_compute_rendered_hours')

    rate = fields.Monetary(currency_field='currency_id',
                           compute='_compute_rate',
                           store=True)

    rate_variance_percent = fields.Float(digits=(12, 4),
                                         compute='_compute_rate_variance_percent',
                                         store=True)

    @api.one
    def _compute_required_hours(self):
        period_start = self.env.context.get('period_start')
        period_end = self.env.context.get('period_end')
        if period_start or period_end:
            attendance_id = self.attendance_ids.filtered(lambda r: r.period_start == period_start and
                                                                   r.period_end == period_end)
            if attendance_id:
                self.required_hours = attendance_id.required_hours
                return

        self.required_hours = 0.0

    @api.one
    def _compute_rendered_hours(self):
        period_start = self.env.context.get('period_start')
        period_end = self.env.context.get('period_end')
        if period_start or period_end:
            attendance_id = self.attendance_ids.filtered(lambda r: r.period_start == period_start and
                                                                   r.period_end == period_end)
            if attendance_id:
                self.rendered_hours = attendance_id.rendered_hours
                return

        self.rendered_hours = 0.0

    @api.one
    @api.depends('position_id', 'revise_rate')
    def _compute_rate(self):
        self.rate = self.revise_rate if self.revise_rate > 0 else self.position_id.unit_rate

    @api.one
    @api.depends('position_id', 'rate')
    def _compute_rate_variance_percent(self):
        if self.position_id.unit_rate == 0 or self.rate == 0:
            self.rate_variance_percent = 0
        else:
            self.rate_variance_percent = ((self.rate - self.position_id.unit_rate) / self.position_id.unit_rate) * 100

    @api.multi
    def toggle_state(self):
        for record in self:
            record.is_mobilized = not record.is_mobilized
            record.state = 'mobilized' if record.is_mobilized else 'not mobilized'
