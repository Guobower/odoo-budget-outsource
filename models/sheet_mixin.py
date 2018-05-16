# -*- coding: utf-8 -*-
import os
import base64
import glob

from odoo import models, fields, api
from odoo.tools import config

from odoo.exceptions import ValidationError


class Sheet(models.AbstractModel):
    _name = 'budget.outsource.sheet'
    _description = 'Sheet'
    _inherit = ['budget.enduser.mixin']

    # CHOICES
    # ----------------------------------------------------------
    STATES = [
        ('draft', 'Draft'),
        ('in progress', 'In Progress'),
        ('cancelled', 'Cancelled'),
        ('closed', 'Closed'),
    ]

    # BASIC FIELDS
    # ----------------------------------------------------------
    state = fields.Selection(selection=STATES, default='draft')
    input_required_hours = fields.Float()
    period_start = fields.Date()
    period_end = fields.Date()
    ramadan_start = fields.Date()
    ramadan_end = fields.Date()

    sheet_filled_filename = fields.Char(string="Filename")
    sheet_filled = fields.Binary(attachment=True)

    # RELATIONSHIPS
    # ----------------------------------------------------------
    po_id = fields.Many2one('budget.purchase.order', string='Purchase Order')
    contractor_id = fields.Many2one('budget.contractor.contractor', string='Contractor')

    # CALCULATED FIELDS
    # ----------------------------------------------------------
    period_string = fields.Char(compute='_compute_period_string',
                                store=True)
    required_hours = fields.Float(compute='_compute_required_hours',
                                  digits=(12, 2))
    required_days = fields.Float(compute='_compute_required_days',
                                 digits=(12, 2))

    @api.one
    @api.depends('period_start', 'period_end')
    def _compute_period_string(self):
        period_start = fields.Date.from_string(self.period_start)
        period_end = fields.Date.from_string(self.period_end)

        if not period_start or not period_end:
            self.period_string = 'n/a'
            return

        self.period_string = '{0:%d-%b-%Y} to {1:%d-%b-%Y}'.format(period_start, period_end)
        return

    @api.one
    @api.depends('period_start', 'period_end', 'ramadan_start', 'ramadan_end')
    def _compute_required_hours(self):
        period_start = fields.Date.from_string(self.period_start)
        period_end = fields.Date.from_string(self.period_end)
        ramadan_start = fields.Date.from_string(self.ramadan_start)
        ramadan_end = fields.Date.from_string(self.ramadan_end)

        if self.input_required_hours > 0:
            self.required_hours = self.input_required_hours
            return

        if not period_start or not period_end:
            self.required_hours = 0
            return

        else:
            total_days = (period_end - period_start).days + 1
            ramadan_days = 0

            if ramadan_start and ramadan_end:
                # if period_start <= ramadan_start <= period_end or \
                #         period_start <= ramadan_end <= period_end:
                start = ramadan_start if period_start <= ramadan_start <= period_end else \
                    period_start
                end = ramadan_end if period_start <= ramadan_end <= period_end else \
                    period_end
                ramadan_days = (end - start).days + 1

            normal_days = total_days - ramadan_days

            # +1 is a corrections factor to count all days within a period
            self.required_hours = normal_days * 48.0 / 7.0 + ramadan_days * 36.0 / 7.0

    @api.one
    @api.depends('period_start', 'period_end')
    def _compute_required_days(self):
        period_start = fields.Date.from_string(self.period_start)
        period_end = fields.Date.from_string(self.period_end)

        if not period_start or not period_end:
            self.period_string = 'n/a'
            return

        self.required_days = (period_end - period_start).days + 1
        return

    # MISC
    # ----------------------------------------------------------
    def get_querysets(self):
        querysets = {}
        return querysets

    def get_context(self):
        # MUST BE INHERITED TO ADD CONTEXT
        module_paths = [i for i in config['addons_path'].split(',')
                        if list(glob.iglob(os.path.join(i, 'budget_outsource')))]

        if len(module_paths) > 1:
            ValidationError('Module should only reside to 1 path')

        module_path = module_paths[0]

        period_start = fields.Date.from_string(self.period_start)
        period_end = fields.Date.from_string(self.period_end)
        ramadan_start = fields.Date.from_string(self.ramadan_start)
        ramadan_end = fields.Date.from_string(self.ramadan_end)

        return {
            'xlsx_pass': 'Tbpc19',
            'form_template_path': os.path.join(module_path, 'budget_outsource', 'sheet_templates'),
            'period_start': period_start,
            'period_end': period_end,
            'ramadan_start': ramadan_start,
            'ramadan_end': ramadan_end,
            'period_string': self.period_string,
            'required_hours': self.required_hours,
            'required_days': self.required_days,
            'contractor_name': self.contractor_id.name
        }

    def attach(self, filename, tmp_file):
        ir_attach = self.env['ir.attachment']
        data = base64.b64encode(tmp_file.getvalue())

        values = dict(
            name=filename,
            datas_fname=filename,
            res_id=self.id,
            res_model=self._name,
            type='binary',
            datas=data,
        )
        ir_attach.create(values)

    # POLYMORPH FUNCTIONS
    # ----------------------------------------------------------
    @api.multi
    def name_get(self):
        result = []
        for r in self:
            result.append((r.id, r.period_string))
        return result
