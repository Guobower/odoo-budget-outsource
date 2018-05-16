# -*- coding: utf-8 -*-
from odoo import models, fields, api


class MobilizeAttendance(models.Model):
    _name = 'budget.outsource.mobilize.attendance'
    _description = 'Mobilize Resource Attendance'
    _inherit = ['mail.thread']

    # BASIC FIELDS
    # ----------------------------------------------------------
    is_verified = fields.Boolean()
    period_start = fields.Date()
    period_end = fields.Date()

    required_hours = fields.Float()
    rendered_hours = fields.Float(default=0.0)
    remarks = fields.Text()

    # RELATED FIELD
    # ----------------------------------------------------------

    # RELATIONSHIPS
    # ----------------------------------------------------------
    mobilize_id = fields.Many2one('budget.outsource.mobilize', string='Mobilized Resource')
    datasheet_id = fields.Many2one('budget.outsource.datasheet', string='Mobilized DataSheet')
