import logging
import time
from json import dumps

import uuid
import time
import numpy as np
from datetime import datetime, date, timedelta
from decimal import Decimal
from cassandra.query import SimpleStatement
from helpers import cassandra_helper

try:
    import simplejson as json
except ImportError:
    import json

from flask import Flask, Blueprint, render_template, request, session, jsonify

# from routes.rest import get_session, \
#     get_solr_session
app = Flask(__name__)

merchant = Blueprint('merchant', __name__)


@merchant.route('/')
def index():
    return render_template('merchant.jinja2')

@merchant.route('/get_blacklisted_merchants')
def get_blacklisted_merchants():
    get_blacklisted_merchants = []
    searchParam = str(request.args.get('queries[search]'))
    if searchParam == 'None':
        get_blacklisted_merchants = cassandra_helper.session.execute(cassandra_helper.session.prepare('''SELECT * FROM datastax_creditcard_demo.blacklist_merchants'''))
    else:
        get_blacklisted_merchants = cassandra_helper.session.execute(cassandra_helper.session.prepare('''SELECT * FROM datastax_creditcard_demo.blacklist_merchants WHERE merchant = '" + searchParams + "'" + '''))
    print len(get_blacklisted_merchants)
    return jsonify(records=get_blacklisted_merchants, queryRecordCount=len(get_blacklisted_merchants), totalRecordCount=len(get_blacklisted_merchants))


@merchant.route('/blacklist_merchant')
def blacklist_merchant():
    merchant = str(request.args.get('merchant'))

    merchantRecords = cassandra_helper.session.execute(cassandra_helper.session.prepare('''SELECT * FROM datastax_creditcard_demo.merchants'''))
    for record in merchantRecords:
        if record['name'] == merchant:
            cassandra_helper.session.execute(cassandra_helper.session.prepare('''
            INSERT INTO datastax_creditcard_demo.blacklist_merchants
                (merchant, city)
            VALUES
                (?,?)
            ''').bind({"merchant": record["name"],
           "city": record["location"]}))
    return jsonify(result="success")

@merchant.route('/whitelist_merchant')
def whitelist_merchant():
    merchant = str(request.args.get('merchant'))

    merchantRecords = cassandra_helper.session.execute(cassandra_helper.session.prepare('''SELECT * FROM datastax_creditcard_demo.merchants'''))
    for record in merchantRecords:
        if record['name'] == merchant:
            cassandra_helper.session.execute(cassandra_helper.session.prepare('''DELETE FROM datastax_creditcard_demo.blacklist_merchants WHERE merchant=? AND city=? ''').bind({
                "merchant":record["name"],
                "city":record["location"],
            }))
    return jsonify(result="success")