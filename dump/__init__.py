# -*- coding: utf-8 -*-
from __future__ import print_function

import csv
import os
import time
import pandas as pd
import datetime as dt

import odoo

DUMP_DIR = os.path.dirname(os.path.realpath(__file__))


def to_bool(data):
    if isinstance(data, str):
        data = data.lower()
        if data == "0" or data == "false":
            return False
        elif data == "1" or data == "true":
            return True

    return NotImplemented


def to_date_format(string):
    # remove time element
    string = string.split(' ')[0]
    try:
        return dt.datetime.strptime(string, '%d/%m/%Y')
    except ValueError:
        return None


def to_dec(data):
    try:
        return float(data)
    except Exception:
        return 0


def shell(dbname):
    local_vars = {
        'openerp': odoo,
        'odoo': odoo,
    }
    with odoo.api.Environment.manage():
        if dbname:
            registry = odoo.registry(dbname)
            with registry.cursor() as cr:
                uid = odoo.SUPERUSER_ID
                ctx = odoo.api.Environment(cr, uid, {})['res.users'].context_get()
                env = odoo.api.Environment(cr, uid, ctx)
                local_vars['env'] = env
                local_vars['self'] = env.user
                cr.rollback()
    return local_vars


class Dumper(object):
    def __init__(self, dumpdir=DUMP_DIR,
                 env=None, model_obj=None, filename=''):
        if env is None:
            raise ValueError

        self.filename = filename
        self.dumpdir = dumpdir
        self.env = env
        self.model_obj = model_obj
        self.sr = 0
        self.sr_new = 0
        self.sr_exist = 0
        self.total = 0
        self.start_time = None

    @property
    def csvpath(self):
        return os.path.join(self.dumpdir, self.filename)

    @property
    def model(self):
        return self.env[self.model_obj]

    def get_total_csv_row(self):
        with open(self.csvpath) as csvfile:
            reader = csv.reader(csvfile)
            total = sum(1 for _ in reader)

        return total - 1

    def progress(self):
        print_string = '\rN: {new:06d} E: {exist:06d} {percent:.2%} - {current}/{total} '.format(
            new=self.sr_new, exist=self.sr_exist,
            percent=float(self.sr) / float(self.total),
            current=self.sr, total=self.total)
        print(print_string, end="")

    def start(self):
        self.start_time = time.time()
        self.total = self.get_total_csv_row()
        print('\n{}'.format(self.model_obj))
        print('=============================================================')

    def end(self):
        lapse_time = time.time() - self.start_time
        print('\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%', end='')
        print('\nLapse Time: {:.5f}sec'.format(lapse_time))
        return lapse_time

    def exist(self):
        self.sr += 1
        self.sr_exist += 1
        self.progress()

    def create(self, data):
        self.model.create(data)
        self.env.cr.commit()
        self.sr += 1
        self.sr_new += 1
        self.progress()


def dump_unit_price(env=None, filename='UnitPrice.csv'):
    dumper = Dumper(env=env, model_obj='outsource.unit.rate', filename=filename)
    dumper.start()
    unit_price_model = dumper.model

    with open(dumper.csvpath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            unit_price = unit_price_model.search([('access_db_id', '=', row["id"])], limit=1)

            if unit_price:
                dumper.exist()
                continue
            else:
                data = {
                    'access_db_id': row["id"],
                    'po_level': row['po_level'],
                    'po_position': row['po_position'],
                    'contractor': row['contractor'],
                    'amount': to_dec(row['amount']),
                    'percent': row['percent'],
                }
                dumper.create(data)
    dumper.end()


def dump_purchase_order(env=None, filename='TechPO.csv'):
    dumper = Dumper(env=env, model_obj='outsource.purchase.order', filename=filename)
    dumper.start()
    po_model = dumper.model

    with open(dumper.csvpath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            po = po_model.search([('access_db_id', '=', row["POID"])])

            if len(po) != 0:
                dumper.exist()
                continue
            else:
                data = {
                    'access_db_id': row["POID"],
                    'po_num': row["PONum"],
                    #                'po_date': to_date_format(row["PODate"]),
                    'po_value': to_dec(row["POValue"]),
                    'contractor': row["Contractor"],
                    'budget': row["Budget"],
                    'capex_commitment_value': to_dec(row["CPXComValue"]),
                    'capex_expenditure_value': to_dec(row["CPXExpValue"]),
                    'opex_value': to_dec(row["OPXValue"]),
                    'revenue_value': to_dec(row["REVValue"]),
                    'task_num': row["TaskNum"],
                    'renew_status': row["RenewStatus"],
                    'po_status': row["POStatus"],
                    'po_remarks': row["PORemarks"],
                    'po_type': row["POType"],
                }
                dumper.create(data)

    dumper.end()


def dump_purchase_order_line(env=None, filename='TechPOLine.csv'):
    dumper = Dumper(env=env, model_obj='outsource.purchase.order.line', filename=filename)
    dumper.start()
    po_line_model = dumper.model

    with open(dumper.csvpath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            po_line = po_line_model.search([('access_db_id', '=', row["POLineID"])])
            if len(po_line) != 0:
                dumper.exist()
                continue
            else:
                po = env['outsource.purchase.order'].search([('access_db_id', '=', row["POID"])])

                if len(po) == 0:
                    print("\nPurchase Order ID# %s Does't Exist" % row["POID"], end='')
                    continue
                elif len(po) > 1:
                    print("\nPurchase Order ID# %s Multiple Record" % row["POID"], end='')
                    continue
                else:
                    data = {
                        'po_id': po[0].id,
                        'access_db_id': row["POLineID"],
                        'line_num': row["POLineNum"],
                        'line_duration': row["POLineDuration"],
                        'line_value': to_dec(row["POLineValue"]),
                        'line_revise_rate': to_dec(row["POLineRValue"]),
                        'line_rate': to_dec(row["POLineRate"]),
                        'line_status': row["POLineStatus"],
                        'line_actuals': row["POLineActuals"],
                        'capex_percent': row["CPXPercent"],
                        'opex_percent': row["OPXPercent"],
                        'revenue_percent': row["REVPercent"],
                    }
                    dumper.create(data)
    dumper.end()


def dump_purchase_order_line_details(env=None, filename='TechPOLineDetail.csv'):
    dumper = Dumper(env=env, model_obj='outsource.purchase.order.line.detail', filename=filename)
    dumper.start()
    po_line_detail_model = dumper.model

    with open(dumper.csvpath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            po_line_detail = po_line_detail_model.search([('access_db_id', '=', row["PODetID"])])
            if len(po_line_detail) != 0:
                dumper.exist()
                continue
            else:
                po_line = env['outsource.purchase.order.line'].search([('access_db_id', '=', row["POLineID"])])
                if len(po_line) == 0:
                    print("\nPurchase Order Line ID# %s Does't Exist" % row["POLineID"], end='')
                    continue
                else:
                    data = {
                        'po_line_id': po_line[0].id,
                        'access_db_id': row["PODetID"],
                        'po_os_ref': row["POOSRef"],
                        'po_position': row["POPosition"],
                        'po_level': row["POLevel"],
                        'po_rate': to_dec(row["PORate"]),
                        'po_revise_rate': to_dec(row["PORRate"]),
                        'rate': to_dec(row["Rate"]),
                        'division': row["Division"],
                        'section': row["Section"],
                        'sub_section': row["SubSection"],
                        'director_name': row["DirName"],
                        'frozen_status': row["FrozenStatus"],
                        'approval_ref_num': row["ApprovalRefNum"],
                        'approval_reason': row["ApprovalReason"],
                        'kpi_2016': row["2016KPI"],
                        'capex_percent': row["CPX%Age"],
                        'opex_percent': row["OPX%Age"],
                        'revenue_percent': row["REV%Age"],
                        'rate_diff_percent_manual': to_dec(row['PORate%IncrManual']),
                        'rate_diff_percent_calculated': to_dec(row['OdooAdditional%'])

                    }
                    dumper.create(data)
    dumper.end()


def dump_invoice(env=None, filename='TechInvoiceMgmt.csv'):
    dumper = Dumper(env=env, model_obj='outsource.invoice', filename=filename)
    dumper.start()
    invoice_model = dumper.model

    with open(dumper.csvpath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            invoice = invoice_model.search([('access_db_id', '=', row['InvID'])], limit=1)
            resource_id = env['outsource.resource'].search([('access_db_id', '=', row['ResID'])], limit=1)
            po_line_detail_id = env['outsource.purchase.order.line.detail'].search(
                [('access_db_id', '=', row['PODetID'])],
                limit=1)
            if not resource_id or not po_line_detail_id:
                continue
            if invoice:
                dumper.exist()
                continue
            else:
                data = {
                    'access_db_id': row['InvID'],
                    'resource_id': resource_id.id,
                    'po_line_detail_id': po_line_detail_id.id,
                    'invoice_date': to_date_format(row['InvMonth']),
                    'invoice_hour': row['InvMonthHrs'],
                    'invoice_claim': row['InvClaimHrs'],
                    'invoice_cert_amount': row['InvCertAmt'],
                    'remarks': row['Remarks']
                }

                dumper.create(data)
    dumper.end()


def dump_resource(env=None, filename='RPT01_ Monthly Accruals - Mobillized.csv'):
    dumper = Dumper(env=env, model_obj='outsource.resource', filename=filename)
    dumper.start()
    resource_model = dumper.model

    with open(dumper.csvpath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            resource = resource_model.search([('access_db_id', '=', row["ResID"])], limit=1)
            po_id = env['outsource.purchase.order'].search([('access_db_id', '=', row["POID"])], limit=1)
            po_line_detail_id = env['outsource.purchase.order.line.detail'].search(
                [('access_db_id', '=', row["PODetID"])], limit=1)

            if resource:
                dumper.exist()
                continue
            else:
                data = {
                    'po_id': po_id.id,
                    'po_line_detail_id': po_line_detail_id.id,
                    'access_db_id': row["ResID"],
                    'res_type': row['ResType'],
                    'res_type_class': row['ResTypeClass'],
                    'agency_ref_num': row['AgencyRefNum'],
                    'res_emp_num': row['ResEmpNum'],
                    'res_full_name': row['ResFullName'],
                    # TODO FIX EMPTY
                    'date_of_join': to_date_format(row['DoJ']),
                    'res_job_title': row['ResJobTitle'],
                    'grade_level': row['GradeLevel'],
                    'po_position': row['POPosition'],
                    'po_level': row['POLevel'],
                    'division': row['Division'],
                    'section': row['Section'],
                    'manager': row['Manager'],
                    'director': row['Director'],
                    'rate': row['Rate'],
                    #                    'po_rate_percent_increase': to_dec(row['PORate%Incr']),
                    'capex_percent': row['CPX%Age'],
                    'capex_rate': row['CAPEXRate'],
                    'opex_percent': row['OPX%Age'],
                    'opex_rate': row['OPEXRate'],
                    'revenue_percent': row['REV%Age'],
                    'revenue_rate': row['REVENUERate'],
                    'remarks': row['Remarks'],
                    'po_num': row['PONum'],
                    'po_value': row['POValue'],
                    'capex_commitment_value': row['CPXComValue'],
                    'opex_value': row['OPXValue'],
                    'revenue_value': row['REVValue'],
                    'contractor': row['Contractor'],
                    'po_os_ref': row['POOSRef'],
                    'has_tool_or_uniform': to_bool(row['ToolsProvided']),
                }
                dumper.create(data)
    dumper.end()


def clear_all(env):
    tables = [
        'outsource_purchase_order',
        'outsource_purchase_order_line',
        'outsource_purchase_order_line_detail',
        'outsource_resource',
        'outsource_invoice',
        'outsource_unit_rate'
    ]
    for table in tables:
        env.cr.execute("TRUNCATE %s CASCADE" % table)

    env.cr.commit()


def start(env):
    dump_unit_price(env)
    dump_purchase_order(env)
    dump_purchase_order_line(env)
    dump_purchase_order_line_details(env)
    dump_resource(env)
    dump_invoice(env)


def start_without_invoice(env):
    dump_unit_price(env)
    dump_purchase_order(env)
    dump_purchase_order_line(env)
    dump_purchase_order_line_details(env)
    dump_resource(env)


def migrate_unit_price(env=None, filename='UnitPrice.csv'):
    dumper = Dumper(env=env, model_obj='budget.outsource.unit.rate', filename=filename)
    dumper.start()
    unit_price_model = dumper.model

    with open(dumper.csvpath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:

            if row['contractor'] == 'REACH':
                contractor_name = 'REACH EMPLOYMENT'
            elif row['contractor'] == 'SHAHID':
                contractor_name = 'SHAHID TECH'
            elif row['contractor'] == 'STAR':
                contractor_name = 'STAR SERVICES'
            else:
                contractor_name = row['contractor']

            contractor_id = env['budget.contractor.contractor'].search([('name', 'like', contractor_name)])

            if len(contractor_id) > 1:
                print(contractor_id.mapped('name'))

            elif not contractor_id:
                continue

            unit_price = unit_price_model.search([
                ('position_name', '=', row['po_position']),
                ('position_level', '=', row['po_level']),
                ('contractor_id', '=', contractor_id.id),

            ], limit=1)

            if unit_price:
                dumper.exist()
                continue
            else:
                data = {
                    'position_name': row['po_position'],
                    'position_level': row['po_level'],
                    'contractor_id': contractor_id.id,
                    'amount': to_dec(row['amount']),
                }
                dumper.create(data)
    dumper.end()


def migrate_purchase_order(env=None, filename='TechPO.csv'):
    dumper = Dumper(env=env, model_obj='budget.purchase.order', filename=filename)
    dumper.start()
    po_model = dumper.model

    with open(dumper.csvpath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            po_id = po_model.search([('no', '=', row["PONum"])])
            if row['Contractor'] == 'REACH':
                contractor_name = 'REACH EMPLOYMENT'
            elif row['Contractor'] == 'SHAHID':
                contractor_name = 'SHAHID TECH'
            elif row['Contractor'] == 'STAR':
                contractor_name = 'STAR SERVICES'
            else:
                contractor_name = row['Contractor']

            contractor_id = env['budget.contractor.contractor'].search([('name', 'like', contractor_name)])

            if len(po_id) != 0:
                dumper.exist()
                continue
            else:
                data = {
                    'no': row["PONum"],
                    'amount': to_dec(row["POValue"]),

                    'contractor_id': contractor_id.id,

                    'remark': row["PORemarks"],
                }
                dumper.create(data)

    dumper.end()


def migrate_position(env=None, filename='TechPOLineDetail.csv'):
    dumper = Dumper(env=env, model_obj='budget.outsource.position', filename=filename)
    dumper.start()
    position_model = dumper.model
    with open(dumper.csvpath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            position = position_model.search([('identifier', '=', row['PODetID'])])

            if position:
                dumper.exist()
                continue

            po_id = env['budget.purchase.order'].search([('no', 'like', row['PONum'])])
            division_id = env['budget.enduser.division'].search([('alias', '=', row['Division'])])

            if len(po_id) != 1 or not len(division_id) != 1:
                continue

            data = {
                'identifier': row['PODetID'],
                'os_ref': row["POOSRef"],
                'name': row["POPosition"],
                'level': row["POLevel"],
                'po_id': False if not po_id else po_id.id,
                'division_id': False if not division_id else division_id.id,
                'capex_percent': row["CPX%Age"],
                'opex_percent': row["OPX%Age"],
                'revenue_percent': row["REV%Age"],
            }
            dumper.create(data)
    dumper.end()


def migrate_resource(env=None, filename='RPT01_ Monthly Accruals - Mobillized.csv'):
    dumper = Dumper(env=env, model_obj='budget.outsource.resource', filename=filename)
    dumper.start()
    resource_model = dumper.model

    with open(dumper.csvpath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            resource = resource_model.search([('identifier', '=', row['ResID'])])

            if resource:
                dumper.exist()
                continue

            if row['Contractor'] == 'REACH':
                contractor_name = 'REACH EMPLOYMENT'
            elif row['Contractor'] == 'SHAHID':
                contractor_name = 'SHAHID TECH'
            elif row['Contractor'] == 'STAR':
                contractor_name = 'STAR SERVICES'
            else:
                contractor_name = row['Contractor']

            contractor_id = env['budget.contractor.contractor'].search([('name', 'like', contractor_name)])

            data = {
                'identifier': row['ResID'],
                'name': row['ResFullName'],
                'type': row['ResType'],
                'type_class': row['ResTypeClass'],
                'agency_ref_num': row['AgencyRefNum'],
                'emp_num': row['ResEmpNum'],
                'date_of_join': to_date_format(row['DoJ']),
                'has_tool_or_uniform': to_bool(row['ToolsProvided']),
                'contractor_id': contractor_id.id,
            }
            dumper.create(data)
    dumper.end()


def migrate_mobilize(env=None, filename='RPT01_ Monthly Accruals - Mobillized.csv'):
    dumper = Dumper(env=env, model_obj='budget.outsource.mobilize', filename=filename)
    dumper.start()
    with open(dumper.csvpath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:

            position_id = env['budget.outsource.position'].search([('identifier', '=', row['PODetID'])])
            resource_id = env['budget.outsource.resource'].search([('identifier', '=', row['ResID'])])
            if not position_id and not resource_id:
                continue

            mobilize_id = env['budget.outsource.mobilize'].search([
                ('position_id', '=', position_id.id),
                ('resource_id', '=', resource_id.id)
            ])

            if mobilize_id:
                dumper.exist()
                continue

            df_position = pd.read_csv(os.path.join(DUMP_DIR, 'TechPOLineDetail.csv'))
            df_position = df_position.fillna(0)
            searched = df_position.loc[df_position['PODetID'] == int(position_id.identifier)]['PORRate']

            data = {
                'position_id': position_id.id,
                'resource_id': resource_id.id,
                'revise_rate': float(searched),
                'state': 'mobilized'
            }
            dumper.create(data)
    dumper.end()


def start_migrate(env):
    migrate_unit_price(env)
    migrate_purchase_order(env)
    migrate_position(env)
    migrate_resource(env)
    migrate_mobilize(env)


if __name__ == '__main__':
    env_vars = shell('dev_db11')
    env = env_vars.get('env')
    start_migrate(env)
