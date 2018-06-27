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
        self.sr_skip = 0
        self.total = 0
        self.start_time = None

    @property
    def csvpath(self):
        return os.path.join(self.dumpdir, self.filename)

    @property
    def model(self):
        return self.env[self.model_obj]

    def log_msg(self, msg):
        log_path = os.path.join(self.dumpdir, 'error.log')

        with open(log_path, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(msg)

    def get_total_csv_row(self):
        with open(self.csvpath) as csvfile:
            reader = csv.reader(csvfile)
            total = sum(1 for _ in reader)

        return total - 1

    def progress(self, msg=None):
        print_string = '\rN: {new:06d} E: {exist:06d} S: {skip:06d} {percent:.2%} - {current}/{total} '.format(
            new=self.sr_new, exist=self.sr_exist, skip=self.sr_skip,
            percent=float(self.sr) / float(self.total),
            current=self.sr, total=self.total)
        print_string += ' %s' % msg if msg else ''
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

    def skip(self, msg):
        self.sr += 1
        self.sr_skip += 1
        self.progress(msg)
        self.log_msg(msg)

    def exist(self):
        self.sr += 1
        self.sr_exist += 1
        self.progress()

    def create(self, data):
        try:
            self.model.create(data)
            self.env.cr.commit()
        except Exception as e:
            self.env.cr.rollback()
            print('{} in {} for {}'.format(e, self.sr, self.filename))

        self.sr += 1
        self.sr_new += 1
        self.progress()


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
                continue

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

    # ============================================================================================================
    # DROP NOT REQUIRED ITEMS
    # ============================================================================================================
    df_mobilize = pd.read_csv(os.path.join(dumper.dumpdir, 'RPT01_ Monthly Accruals - Mobillized.csv'))[['POID']]
    df_po = pd.read_csv(os.path.join(dumper.dumpdir, 'TechPO.csv'))
    required_columns = list(df_po.columns)

    df_po = pd.merge(left=df_mobilize, right=df_po,
                     how='left', left_on='POID', right_on='POID')

    df_po = df_po[required_columns]
    df_po.drop_duplicates(df_po.columns, inplace=True)

    df_po.to_csv(os.path.join(dumper.dumpdir, 'TechPO.csv'), index=False)
    # ============================================================================================================
    # END DROP NOT REQUIRED ITEMS
    # ============================================================================================================

    dumper.start()
    po_model = dumper.model

    with open(dumper.csvpath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            po_num = row["PONum"].strip()
            po_num = po_num if '-' else po_num + '-0'
            po_id = po_model.search([('no', 'like', po_num)])

            if row['Contractor'] == 'REACH':
                contractor_name = 'REACH EMPLOYMENT SERVICES'
            elif row['Contractor'] == 'SHAHID':
                contractor_name = 'SHAHID TECH CONT CO LLC'
            elif row['Contractor'] == 'STAR':
                contractor_name = 'STAR SERVICES L.L.C'
            else:
                contractor_name = row['Contractor']

            contractor_id = env['budget.contractor.contractor'].search([('name', '=', contractor_name)])

            if len(po_id) != 0:
                data = {
                    'contractor_id': contractor_id.id,
                }
                po_id.write(data)

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

    # ============================================================================================================
    # ADD POID IN THE POSITIONS
    # ============================================================================================================
    df_po_detail = pd.read_csv(os.path.join(dumper.dumpdir, 'TechPOLineDetail.csv'))

    if 'PONum' in df_po_detail.columns:
        df_po_detail.drop(['PONum'], 1, inplace=True)

    df_po_line = pd.read_csv(os.path.join(dumper.dumpdir, 'TechPOLine.csv'))[['POLineID', 'POID']]
    df_po = pd.read_csv(os.path.join(dumper.dumpdir, 'TechPO.csv'))[['PONum', 'POID']]

    required_columns = list(df_po_detail.columns) + ['PONum']
    df_po_detail = pd.merge(left=df_po_detail, right=df_po_line,
                            how='left', left_on='POLineID', right_on='POLineID')

    df_po_detail = pd.merge(left=df_po_detail, right=df_po,
                            how='left', left_on='POID', right_on='POID')

    df_po_detail = df_po_detail[required_columns]
    df_po_detail.to_csv(os.path.join(dumper.dumpdir, 'TechPOLineDetail.csv'), index=False)
    # ============================================================================================================
    # END ADD POID IN THE POSITIONS
    # ============================================================================================================

    # ============================================================================================================
    # DROP NOT REQUIRED ITEMS
    # ============================================================================================================
    df_mobilize = pd.read_csv(os.path.join(dumper.dumpdir, 'RPT01_ Monthly Accruals - Mobillized.csv'))[['PODetID']]
    df_po_detail = pd.read_csv(os.path.join(dumper.dumpdir, 'TechPOLineDetail.csv'))
    required_columns = list(df_po_detail.columns)

    df_po_detail = pd.merge(left=df_mobilize, right=df_po_detail,
                     how='left', left_on='PODetID', right_on='PODetID')

    df_po_detail = df_po_detail[required_columns]
    df_po_detail.drop_duplicates(df_po_detail.columns, inplace=True)

    df_po_detail.to_csv(os.path.join(dumper.dumpdir, 'TechPOLineDetail.csv'), index=False)
    # ============================================================================================================
    # END DROP NOT REQUIRED ITEMS
    # ============================================================================================================

    dumper.start()
    position_model = dumper.model
    with open(dumper.csvpath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            position = position_model.search([('identifier', '=', row['PODetID'])])

            if position:
                dumper.exist()
                continue

            po_id = env['budget.purchase.order'].search([('no', 'like', row['PONum'].strip())])
            division_id = env['budget.enduser.division'].search([('alias', '=', row['Division'])])

            if len(po_id) != 1:
                msg = 'PO {} has {} records in the system'.format(row['PONum'], len(po_id))
                dumper.skip(msg)
                continue

            if len(division_id) != 1:
                msg = 'DIVISION {} has {} records in the system'.format(row['Division'], len(division_id))
                dumper.skip(msg)
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

            revise_rate = int(row['Rate']) if not int(position_id.unit_rate) == row['Rate'] else 0

            data = {
                'position_id': position_id.id,
                'resource_id': resource_id.id,
                'revise_rate': revise_rate,
                'state': 'mobilized',
                'manager': row['Manager'],
                'director': row['Director']
            }
            dumper.create(data)
    dumper.end()


def migration_correction(env):
    po_ids = env['budget.purchase.order'].search([
        ('outsource_position_ids', '!=', False)
    ])

    contract_ids = env['budget.contractor.contract'].search([
        ('contract_ref', 'like', '713H')
    ])

    for i in [po_ids, contract_ids]:
        i.write({
            'is_outsource': True
        })

    unit_rate_ids = env['budget.outsource.unit.rate'].search([])

    for unit_rate_id in unit_rate_ids:
        contract_ids = env['budget.contractor.contract'].search([
            ('contract_ref', 'like', '713H'),
            ('contractor_id', '=', unit_rate_id.contractor_id.id)
        ])
        for contract_id in contract_ids:
            unit_rate_id.contract_id = contract_id
    env.cr.commit()


def start_migrate(env):
    migrate_unit_price(env)
    migrate_purchase_order(env)
    migrate_position(env)
    migrate_resource(env)
    migrate_mobilize(env)
    migration_correction(env)
