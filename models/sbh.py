# -*- coding: utf-8 -*-
import base64
import io

from odoo import models, fields, api
from odoo.exceptions import ValidationError

import pandas as pd
from openpyxl.styles import Protection

from .utils import *
from .utils import load_workbook
from .utils import odoo_to_pandas_list


class Sbh(models.Model):
    _name = 'budget.outsource.sbh'
    _description = 'SBH'
    _inherit = ['budget.outsource.sheet']

    # CHOICES
    # ----------------------------------------------------------

    # BASIC FIELDS
    # ----------------------------------------------------------

    # RELATIONSHIPS
    # ----------------------------------------------------------

    # MISC
    # ----------------------------------------------------------
    @api.one
    def generate_sbh(self):
        pass

    @api.one
    def analyse_sbh(self):
        pass
