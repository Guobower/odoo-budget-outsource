# -*- coding: utf-8 -*-
from odoo import models, fields, api

from odoo.exceptions import ValidationError
from ..sheet_creator import Sbh, DataSheet

XLSX_PASS = 'tbpc19'


class SheetWizard(models.Model):
    _name = 'budget.outsource.sheet.wizard'
    _rec_name = 'name'
    _description = 'Sheet'
    _inherit = ['budget.enduser.mixin']

    # CHOICES
    # ----------------------------------------------------------
    GENERATOR_CHOICES = [
        (1, 'SBH for ALL PO NUMBER'),
        (2, 'SBH per PO NUMBER'),
        (3, 'SBH per CONTRACTOR'),
        (4, 'SBH per DIVISION'),
        (5, 'DATASHEET for ALL CONTRACTOR'),
        (6, 'DATASHEET per CONTRACTOR'),
    ]

    TYPES = [
        ('datasheet', 'DATASHEET'),
        ('sbh', 'SBH')
    ]

    # BASIC FIELDS
    # ----------------------------------------------------------
    generator_choice = fields.Selection(selection=GENERATOR_CHOICES)

    name = fields.Char()
    type = fields.Selection(selection=TYPES)
    total_required_hours = fields.Integer()
    period_start = fields.Date()
    period_end = fields.Date()
    ramadan_start = fields.Date()
    ramadan_end = fields.Date()

    # RELATIONSHIPS
    # ----------------------------------------------------------
    po_id = fields.Many2one('budget.purchase.order', string='Purchase Order')
    contractor_id = fields.Many2one('budget.contractor.contractor', string='Contractor')

    # BUTTONS
    # ----------------------------------------------------------
    @api.one
    def generate_sheet(self):
        period_start = fields.Date.from_string(self.period_start)
        period_end = fields.Date.from_string(self.period_end)
        ramadan_start = fields.Date.from_string(self.ramadan_start)
        ramadan_end = fields.Date.from_string(self.ramadan_end)
        total_required_hours = self.total_required_hours

        if self.generator_choice in [1, 2, 3, 4]:
            obj = Sbh(env=self.env, form_name="SBH-FORM.xlsx", xlsx_pass=XLSX_PASS)

        elif self.generator_choice in [5, 6]:
            obj = DataSheet(env=self.env, form_name="DATASHEET.xlsx", xlsx_pass=XLSX_PASS)

        else:
            raise ValidationError('Invalid Choice')

        kargs = {
            'period_start': period_start,
            'period_end': period_end,
            'ramadan_start': ramadan_start,
            'ramadan_end': ramadan_end,
            'total_required_hours': total_required_hours
        }

        if self.generator_choice == 1:
            obj.make_sbh_per_contractor('all', **kargs)

        elif self.generator_choice == 2:
            obj.make_sbh_per_po(self.po_id.po_num, **kargs)

        elif self.generator_choice == 3:
            obj.make_sbh_per_contractor(self.contractor, **kargs)

        elif self.generator_choice == 4:
            obj.make_sbh_per_division(self.po_id.po_num, **kargs)

        elif self.generator_choice == 5:
            obj.make_datasheet_per_contractor('all', **kargs)

        elif self.generator_choice == 6:
            obj.make_datasheet_per_contractor(self.contractor, **kargs)

        zip_path = obj.make_zip()

        obj.attach(self.env, self.id, self._name, zip_path)
        obj.cleanup()
