# -*- coding: utf-8 -*-
import io

from odoo import models, fields, api
from odoo.exceptions import ValidationError

import pandas as pd
from openpyxl.styles import Protection

from .utils import *
from .utils import load_workbook
from .utils import odoo_to_pandas_list


class DataSheet(models.TransientModel):
    _name = 'budget.outsource.datasheet.upload.wizard'
    _description = 'Data Sheet Upload Wizard'

    # CHOICES
    # ----------------------------------------------------------
    filename = fields.Char(string="File Name")
    attachment = fields.Binary()

    # BASIC FIELDS
    # ----------------------------------------------------------

    # RELATIONSHIPS
    # ----------------------------------------------------------

    # MISC
    # ----------------------------------------------------------
