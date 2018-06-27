# -*- coding: utf-8 -*-
import os
import base64
import glob

from odoo import models, fields, api
from odoo.tools import config

from odoo.exceptions import ValidationError

MOBILIZE_COLUMNS = {
    'id': 'id',
    'manager': 'manager',
    'director': 'director',
    'rate': 'rate',
    'rate_variance_percent': 'rate_variance_percent',

    'position_id.identifier': 'positionID',
    'position_id.os_ref': 'os_ref',
    'position_id.name': 'position_name',
    'position_id.level': 'position_level',
    'position_id.division_id.alias': 'division_alias',
    'position_id.section_id.name': 'section_name',
    'position_id.unit_rate': 'unit_rate',
    'position_id.po_id.no': 'po_num',

    'resource_id.identifier': 'resID',
    'resource_id.agency_ref_num': 'agency_ref_num',
    'resource_id.name': 'resource_name',
    'resource_id.date_of_join': 'date_of_join',
    'resource_id.has_tool_or_uniform': 'has_tool_or_uniform'
}

XLSX_PASS = 'tbpc19'


class SheetMixin(models.AbstractModel):
    _name = 'budget.outsource.sheet.mixin'
    _description = 'Sheet'
    _inherit = ['budget.enduser.mixin']

    # CHOICES
    # ----------------------------------------------------------
    STATES = [
        ('draft', 'Draft'),
        ('in progress', 'In Progress'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
        ('closed', 'Closed'),
    ]

    # BASIC FIELDS
    # ----------------------------------------------------------
    state = fields.Selection(selection=STATES, default='draft')
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
                                  inverse='_inverse_required_hours',
                                  store=True,
                                  digits=(12, 2))
    required_days = fields.Float(compute='_compute_required_days',
                                 store=True,
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

    @api.one
    def _inverse_required_hours(self):
        pass

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

        return {
            'xlsx_pass': XLSX_PASS,
            'form_template_path': os.path.join(module_path, 'budget_outsource', 'sheet_templates'),
            'period_start': fields.Date.from_string(self.period_start),
            'period_end': fields.Date.from_string(self.period_end),
            'ramadan_start': False if not self.ramadan_start else fields.Date.from_string(self.ramadan_start),
            'ramadan_end': False if not self.ramadan_end else fields.Date.from_string(self.ramadan_end),
            'period_string': self.period_string,
            'required_hours': self.required_hours,
            'required_days': self.required_days,
            'contractor_name': self.contractor_id.name,
            'contractor_alias': self.contractor_id.alias
        }

    @api.one
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

    # Button
    # ----------------------------------------------------------
    @api.one
    def reset(self):
        ir_attach = self.env['ir.attachment'].search([
            ('res_id', '=', self.id),
            ('res_model', '=', self._name)
        ])

        if ir_attach:
            ir_attach.unlink()

        self.state = 'draft'

    # ACTION METHODS
    # ----------------------------------------------------------
    @api.multi
    def action_show_attendance(self, domain):
        """ Open a window to make enhancement
        """
        tree = self.env.ref('budget_outsource.view_tree_mobilize_with_attendance')
        context = {
            'period_start': self.period_start,
            'period_end': self.period_end
        }

        return {
            'name': 'Attendance',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'budget.outsource.mobilize',
            'views': [(tree.id, 'tree')],
            'view_id': tree.id,
            'target': 'current',
            'context': context,
            'domain': domain or []
        }

    # POLYMORPH FUNCTIONS
    # ----------------------------------------------------------
    @api.multi
    def name_get(self):
        result = []
        for r in self:
            result.append((r.id, r.period_string))
        return result
