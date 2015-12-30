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

user = Blueprint('user', __name__)

@user.route('/')
def index():
    return render_template('user.jinja2')


@user.route('/get_blacklisted_users')
def get_blacklisted_users():
    blacklisted_users = []
    searchParam = str(request.args.get('queries[search]'))
    if searchParam == 'None':
        blacklisted_users = cassandra_helper.session.execute(cassandra_helper.session.prepare('''SELECT * FROM datastax_creditcard_demo.blacklist_cards'''))
    else:
        blacklisted_users = cassandra_helper.session.execute(cassandra_helper.session.prepare('''SELECT * FROM datastax_creditcard_demo.blacklist_cards WHERE issuer = '" + searchParams + "'" + '''))
    return jsonify(records=blacklisted_users, queryRecordCount=len(blacklisted_users), totalRecordCount=len(blacklisted_users))

@user.route('/get_user')
def get_user():
    cc_no = request.args.get('cc_no')
    userRecord = []
    userRecord = cassandra_helper.session.execute(cassandra_helper.session.prepare('''SELECT * FROM datastax_creditcard_demo.users WHERE cc_no=?''').bind({'cc_no':cc_no}))
    return jsonify(results=userRecord)


@user.route('/blacklist_user')
def blacklist_user():
    cc_no = str(request.args.get('cc_no'))

    records = cassandra_helper.session.execute(cassandra_helper.session.prepare('''SELECT * FROM datastax_creditcard_demo.users WHERE cc_no = ?''').bind({"cc_no":cc_no}))
    if records != []:
        cassandra_helper.session.execute(cassandra_helper.session.prepare('''
            INSERT INTO datastax_creditcard_demo.blacklist_cards
                (cc_no, dummy)
            VALUES
                (?, ?)
            ''').bind({"cc_no": records[0]["cc_no"], "dummy":""}))



    return jsonify(result="success")



    return "success"
@user.route('/whitelist_user')
def whitelist_user():
    cc_no = str(request.args.get('cc_no'))
    records = cassandra_helper.session.execute(cassandra_helper.session.prepare('''SELECT * FROM datastax_creditcard_demo.users WHERE cc_no = ?''').bind({"cc_no":cc_no}))
    if records != []:
        cassandra_helper.session.execute(cassandra_helper.session.prepare('''DELETE FROM datastax_creditcard_demo.blacklist_cards WHERE cc_no=?''').bind({
            "cc_no":cc_no,
        }))
    return jsonify(result="success")