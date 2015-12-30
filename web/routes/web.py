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

web = Blueprint('web', __name__)
prepared_statements = None


def preflight_check():
    global prepared_statements
    prepared_statements = {}
    prepared_statements['get_transactions'] = cassandra_helper.session.prepare('''
        SELECT transaction_id,cc_no, merchant,location FROM datastax_creditcard_demo.transactions
    ''')

    prepared_statements['get_credit_cards_id'] = cassandra_helper.session.prepare('''
        SELECT * FROM datastax_creditcard_demo.transactions WHERE transaction_id = ?
    ''')

    prepared_statements['get_transactions_merchant_date_line'] = cassandra_helper.session.prepare('''
        SELECT * FROM datastax_creditcard_demo.credit_card_transactions_by_merchant_date
    ''')
    prepared_statements['get_transactions_merchant'] = cassandra_helper.session.prepare('''
        SELECT * FROM datastax_creditcard_demo.credit_card_transactions_by_merchant_date WHERE merchant = ?
    ''')

    prepared_statements['get_blacklisted_transactions'] = cassandra_helper.session.prepare('''
        SELECT transaction_id FROM datastax_creditcard_demo.blacklist_transactions WHERE transaction_id = ?
    ''')

    prepared_statements['get_blacklisted_merchant'] = cassandra_helper.session.prepare('''
        SELECT * FROM datastax_creditcard_demo.blacklist_merchants
    ''')

    prepared_statements['insert_transaction_merchant_date'] = cassandra_helper.session.prepare('''
    INSERT INTO datastax_creditcard_demo.credit_card_transactions_by_merchant_date
        (cc_no, date, transaction_id, merchant, amount)
    VALUES
        (?, ?, now(), ?, ?)
    ''')
    prepared_statements['insert_transaction'] = cassandra_helper.session.prepare('''
    INSERT INTO datastax_creditcard_demo.transactions
        (cc_no, transaction_id, location, merchant, amount, status, notes)
    VALUES
        (?, now(),?, ?,?,?,?)
    ''')
    prepared_statements['blacklist_transaction'] = cassandra_helper.session.prepare('''
    INSERT INTO datastax_creditcard_demo.blacklist_transactions
        (dummy, transaction_id)
    VALUES
        (?, ?)
    ''')

    prepared_statements['get_merchant_trans_counter'] = cassandra_helper.session.prepare('''SELECT * FROM datastax_creditcard_demo.trans_merchant_counter''')


@web.route('/')
def index():
    preflight_check()
    transactions = cassandra_helper.session.execute(
        prepared_statements['get_transactions'])
    return render_template('index.jinja2', results=transactions)





@web.route('/get_cc_by_merchant')
def get_cc_by_merchant():
    preflight_check()
    # startEpoch = request.args.get('startDate')
    # endEpoch = request.args.get('endDate')
    # startdate = datetime.fromtimestamp(float(startEpoch))
    # enddate = datetime.fromtimestamp(float(endEpoch))


    merchant_counts = cassandra_helper.session.execute(prepared_statements['get_merchant_trans_counter'])


    description = ["PieChart", "Pie"]

    data = []
    for merchant in merchant_counts:
        data.append([merchant["merchant_name"], merchant["total"]])
    return dumps([description] + data)

@web.route('/get_cc_transactions')
def get_cc_transactions():
    preflight_check()


    tableFields = ["date", "cc_no", "merchant", "transaction_id", "amount"]
    sortingFilter = tableFields[0]
    sortingDirection = 'DESC'
    for field in tableFields:
        requestArg = request.args.get("sorts[" + field + "]")
        if requestArg == '1':
            sortingFilter = field
            sortingDirection = 'ASC'
        elif requestArg == '-1':
            sortingFilter = field



    # startEpoch = request.args.get('startDate')
    # endEpoch = request.args.get('endDate')
    # startdate = datetime.fromtimestamp(float(startEpoch))
    # enddate = datetime.fromtimestamp(float(endEpoch))


    perPage = int(request.args.get('perPage'))
    page = int(request.args.get('page'))
    searchParam = request.args.get('queries[search]')

    finalTransactions = []
    if searchParam == None:
        statement = SimpleStatement("SELECT " + ",".join(tableFields) + " FROM datastax_creditcard_demo.credit_card_transactions_by_merchant_date",fetch_size=((page-1) * perPage + perPage))
    else:
        statement = SimpleStatement("SELECT " + ",".join(tableFields) + " FROM datastax_creditcard_demo.credit_card_transactions_by_merchant_date WHERE cc_no='" + searchParam + "' ALLOW FILTERING",fetch_size=((page-1) * perPage + perPage))
    get_paged_transactions = cassandra_helper.session.execute(statement)


    transaction_count = cassandra_helper.session.execute(cassandra_helper.session.prepare('''SELECT * FROM datastax_creditcard_demo.trans_counter'''))[0]["total"]
    i = 0
    for val in get_paged_transactions:
        transaction_date = datetime.fromtimestamp(float(val["date"]))

        if (page-1) * perPage <= i < ((page-1) * perPage + perPage):
            if cassandra_helper.session.execute(cassandra_helper.session.prepare('''SELECT transaction_id FROM datastax_creditcard_demo.blacklist_transactions WHERE transaction_id = ?''')
                                                        .bind({"transaction_id": val["transaction_id"]})) == []:
                finalTransactions.append({
                    "cc_no": val["cc_no"],
                    "merchant": val["merchant"],
                    "date": str(datetime.fromtimestamp(float(val["date"])).date()),

                    "amount":val["amount"],
                    "transaction_id": val["transaction_id"],
                    "blacklist": "false",
                });
            else:
                finalTransactions.append({
                    "cc_no": val["cc_no"],
                    "merchant": val["merchant"],
                    "date": str(datetime.fromtimestamp(float(val["date"])).date()),

                    "amount":val["amount"],
                    "transaction_id": val["transaction_id"],
                    "blacklist": "true",
                });
        elif i > ((page-1) * perPage + perPage):
            break;


        i += 1


    return jsonify(records=finalTransactions, queryRecordCount=transaction_count, totalRecordCount=transaction_count)



@web.route('/get_transaction_count')
def get_transaction_count():
    preflight_check()
    transaction_counter = cassandra_helper.session.execute(cassandra_helper.session.prepare('''SELECT * FROM datastax_creditcard_demo.trans_counter'''))
    min_transaction_counter = cassandra_helper.session.execute(cassandra_helper.session.prepare('''SELECT * FROM datastax_creditcard_demo.minute_trans_counter'''))
    hour_transaction_counter = cassandra_helper.session.execute(cassandra_helper.session.prepare('''SELECT * FROM datastax_creditcard_demo.hour_trans_counter'''))
    day_transaction_counter = cassandra_helper.session.execute(cassandra_helper.session.prepare('''SELECT * FROM datastax_creditcard_demo.day_trans_counter'''))
    return jsonify(transaction_count=transaction_counter[0]['total'],
                   min_transaction_count=min_transaction_counter[0]['total'],
                   hour_transaction_count=hour_transaction_counter[0]['total'],
                   day_transaction_count=day_transaction_counter[0]['total'])

@web.route('/get_cc_by_date')
def get_cc_by_date():
    preflight_check()
    startEpoch = request.args.get('startDate')
    endEpoch = request.args.get('endDate')

    transactions_merchant = cassandra_helper.session.execute(prepared_statements['get_transactions_merchant_date_line'])

    startdate = datetime.fromtimestamp(float(startEpoch))
    enddate = datetime.fromtimestamp(float(endEpoch))
    dates = []

    while startdate.date() <= enddate.date():
        dates.append([str(startdate.date()), 0])
        startdate = startdate + timedelta(days=1)

    for transaction in transactions_merchant:
        for j in range(0, len(dates)):
            dateToLookAt = dates[j][0]
            if str(datetime.fromtimestamp(float(transaction["date"])).date()) == dateToLookAt:
    #             if cassandra_helper.session.execute(cassandra_helper.session.prepare('''
    #     SELECT * FROM datastax_creditcard_demo.blacklist_transactions WHERE transaction_id = ?
    # ''').bind({"transaction_id": transaction["transaction_id"]})) == []:
                dates[j][1] += 1
                # else:
                #     dates[j][2] += 1



    return jsonify(results=dates)

@web.route('/mark_transaction_fraud')
def mark_transaction_fraud():
    preflight_check()
    trans_id = request.args.get('transaction_id')
    transaction_id = uuid.UUID(trans_id)
    cassandra_helper.session.execute(prepared_statements['blacklist_transaction'].bind({"dummy": request.args.get("reason"),"transaction_id": transaction_id}))
    return "success"

@web.route('/approve_transaction')
def approve_transaction():
    preflight_check()
    trans_id = request.args.get('transaction_id')
    transaction_id = uuid.UUID(trans_id)
    cassandra_helper.session.execute(cassandra_helper.session.prepare('''DELETE FROM datastax_creditcard_demo.blacklist_transactions WHERE transaction_id = ?''').bind({"transaction_id": transaction_id}))
    return "success"



@web.route('/transactions_modal')
def transactions_modal():
    preflight_check()

    transaction_id = uuid.UUID(request.args.get('transaction_id'))
    transaction = cassandra_helper.session.execute(prepared_statements['get_credit_cards_id'].bind({"transaction_id": transaction_id}))

    return render_template('transactions_modal.jinja2', transactions=transaction[0])

@web.route('/get_transactions_by_merchant')
def get_transactions_by_merchant():
    preflight_check()
    merchant = str(request.args.get('merchant'))
    perPage = int(request.args.get('perPage'))
    page = int(request.args.get('page'))
    searchParam = str(request.args.get('queries[search]'))

    finalTransactions = []
    if searchParam == 'None':
        statement = SimpleStatement("SELECT * FROM datastax_creditcard_demo.credit_card_transactions_by_merchant_date WHERE merchant = '" + merchant +"'",fetch_size=((page-1) * perPage + perPage))
    else:
        statement = SimpleStatement("SELECT * FROM datastax_creditcard_demo.credit_card_transactions_by_merchant_date WHERE merchant = '" + merchant +"' " + "AND cc_no = '" + searchParam + "'",fetch_size=((page-1) * perPage + perPage))
    get_paged_transactions = cassandra_helper.session.execute(statement)


    merchant_counts = cassandra_helper.session.execute(cassandra_helper.session.prepare('''SELECT * FROM datastax_creditcard_demo.trans_merchant_counter'''))
    merchant_count = 0
    for count in merchant_counts:
        if count["merchant_name"] == merchant:
            merchant_count = count["total"]
            break;
    i = 0
    for val in get_paged_transactions:
        # transaction_date = datetime.fromtimestamp(float(val["date"]))
        # if transaction_date.date() <= enddate.date() and transaction_date.date() >= startdate.date():
        if (page-1) * perPage <= i < ((page-1) * perPage + perPage):

            if cassandra_helper.session.execute(cassandra_helper.session.prepare('''SELECT transaction_id FROM datastax_creditcard_demo.blacklist_transactions WHERE transaction_id = ?''')
                                                        .bind({"transaction_id": val["transaction_id"]})) == []:
                finalTransactions.append({
                     "cc_no": val["cc_no"],
                    "merchant": val["merchant"],
                    "date": str(datetime.fromtimestamp(float(val["date"])).date()),
                    "transaction_id": val["transaction_id"],
                    "amount": val["amount"],
                    "blacklist": "false",
                });
            else:
                    finalTransactions.append({
                    "cc_no": val["cc_no"],
                    "merchant": val["merchant"],
                    "date": str(datetime.fromtimestamp(float(val["date"])).date()),
                    "transaction_id": val["transaction_id"],
                    "amount": val["amount"],
                    "blacklist": "true",
                });


        elif i > ((page-1) * perPage + perPage):
            break;

        i += 1
    return jsonify(records=finalTransactions, queryRecordCount=merchant_count, totalRecordCount=merchant_count)
#
# def get_transactions_by_merchant():
#     preflight_check()
#     cc_no = str(request.args.get('cc_no'))
#     perPage = int(request.args.get('perPage'))
#     page = int(request.args.get('page'))
#     searchParam = str(request.args.get('queries[search]'))
#
#     finalTransactions = []
#     # if searchParam == 'None':
#     statement = SimpleStatement("SELECT * FROM datastax_creditcard_demo.credit_card_transactions_by_merchant_date WHERE cc_no = '" + cc_no +"'",fetch_size=((page-1) * perPage + perPage))
#     # else:
#     #     statement = SimpleStatement("SELECT * FROM datastax_creditcard_demo.credit_card_transactions_by_issuer_date WHERE cc_no = '" + cc_no +"' " + "AND cc_no = '" + searchParam + "'",fetch_size=((page-1) * perPage + perPage))
#     get_paged_transactions = cassandra_helper.session.execute(statement)
#
#
#     merchant_counts = cassandra_helper.session.execute(cassandra_helper.session.prepare('''SELECT * FROM datastax_creditcard_demo.trans_merchant_counter'''))
#     merchant_count = 0
#     for count in merchant_counts:
#         if count["issuer_name"] == merchant:
#             issuer_count = count["total"]
#             break;
#     i = 0
#     for val in get_paged_transactions:
#         # transaction_date = datetime.fromtimestamp(float(val["date"]))
#         # if transaction_date.date() <= enddate.date() and transaction_date.date() >= startdate.date():
#         if (page-1) * perPage <= i < ((page-1) * perPage + perPage):
#
#             if cassandra_helper.session.execute(cassandra_helper.session.prepare('''SELECT transaction_id FROM datastax_creditcard_demo.blacklist_transactions WHERE transaction_id = ?''')
#                                                         .bind({"transaction_id": val["transaction_id"]})) == []:
#                 finalTransactions.append({
#                      "cc_no": val["cc_no"],
#                     "issuer": val["issuer"],
#                     "date": str(datetime.fromtimestamp(float(val["date"])).date()),
#                     "transaction_id": val["transaction_id"],
#                     "amount": val["amount"],
#                     "blacklist": "false",
#                 });
#             else:
#                     finalTransactions.append({
#                     "cc_no": val["cc_no"],
#                     "issuer": val["issuer"],
#                     "date": str(datetime.fromtimestamp(float(val["date"])).date()),
#                     "transaction_id": val["transaction_id"],
#                     "amount": val["amount"],
#                     "blacklist": "true",
#                 });
#
#
#         elif i > ((page-1) * perPage + perPage):
#             break;
#
#         i += 1
#     return jsonify(records=finalTransactions, queryRecordCount=issuer_count, totalRecordCount=issuer_count)
