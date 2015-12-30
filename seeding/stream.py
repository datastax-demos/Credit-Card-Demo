#!/usr/bin/env python

import csv
import itertools
import time
import random
import uuid
from random import randint, uniform
from datetime import datetime, date, timedelta

from cassandra.cluster import Cluster
from cassandra.query import ordered_dict_factory

ip_addresses = '127.0.0.1'
ip_addresses = ip_addresses.split(',')
cluster = Cluster(ip_addresses)
session = cluster.connect()
session.row_factory = ordered_dict_factory

previous_minute = datetime.now().minute
previous_hour = datetime.now().hour
previous_day = datetime.now().day

get_trans_counter = session.prepare('''SELECT * FROM datastax_creditcard_demo.trans_counter''')
get_minute_trans_counter = session.prepare('''SELECT * FROM datastax_creditcard_demo.minute_trans_counter''')
get_hour_trans_counter = session.prepare('''SELECT * FROM datastax_creditcard_demo.hour_trans_counter''')
get_day_trans_counter = session.prepare('''SELECT * FROM datastax_creditcard_demo.day_trans_counter''')

incr_trans_counter = session.prepare('''UPDATE datastax_creditcard_demo.trans_counter
                                                                                  SET total = total + 1
                                                                                  WHERE date=?''')
incr_minute_trans_counter = session.prepare('''UPDATE datastax_creditcard_demo.minute_trans_counter
                                                                                  SET total = total + 1
                                                                                  WHERE date=?''')
reset_minute_trans_counter = session.prepare('''UPDATE datastax_creditcard_demo.minute_trans_counter
                                                                                  SET total = total + ?
                                                                                  WHERE date=?''')
incr_hour_trans_counter = session.prepare('''UPDATE datastax_creditcard_demo.hour_trans_counter
                                                                                  SET total = total + 1
                                                                                  WHERE date=?''')
reset_hour_trans_counter = session.prepare('''UPDATE datastax_creditcard_demo.hour_trans_counter
                                                                                  SET total = total + ?
                                                                                  WHERE date=?''')
incr_day_trans_counter = session.prepare('''UPDATE datastax_creditcard_demo.day_trans_counter
                                                                                  SET total = total + 1
                                                                                  WHERE date=?''')
reset_day_trans_counter = session.prepare('''UPDATE datastax_creditcard_demo.day_trans_counter
                                                                                  SET total = total + ?
                                                                                  WHERE date=?''')
# incr_hour_trans_counter = session.prepare('''UPDATE datastax_creditcard_demo.trans_counter
#                                                                                   SET total = total + 1
#                                                                                   WHERE hour=?''')
# incr_day_trans_counter = session.prepare('''UPDATE datastax_creditcard_demo.trans_counter
#                                                                                   SET total = total + 1
#                                                                                   WHERE day=?''')

def stream_quotes():
    print 'Streaming quotes and latest...'



    insert_transaction_merchant_date = session.prepare('''
    INSERT INTO datastax_creditcard_demo.credit_card_transactions_by_merchant_date
        (cc_no, date, transaction_id, merchant, amount)
    VALUES
        (?, ?, ?, ?, ?)
    ''')
    insert_transaction = session.prepare('''
    INSERT INTO datastax_creditcard_demo.transactions
        (cc_no, transaction_id, location, merchant, amount, status, notes)
    VALUES
        (?, ?,?, ?,?,?,?)
    ''')
    insert_transaction_counter = session.prepare('''
    INSERT INTO datastax_creditcard_demo.transactions
        (cc_no, transaction_id, location, merchant, amount, status, notes)
    VALUES
        (?, ?,?, ?,?,?,?)
    ''')
    blacklist_transaction = session.prepare('''
    INSERT INTO datastax_creditcard_demo.blacklist_transactions
        (dummy, transaction_id)
    VALUES
        (?, ?)
    ''')

    insert_merchant = session.prepare('''INSERT INTO datastax_creditcard_demo.merchants
          (id, name, location)
        VALUES
          (?,?, ?)''')
    set_merchant_counter = session.prepare('''UPDATE datastax_creditcard_demo.trans_merchant_counter  SET total = total + ? WHERE merchant_id=? AND merchant_name=?''')

    merchants = [{"id":"e3f3e2a4-bdee-46e0-990b-2fa95da0036f",
                "name":"7-ELEVEN#22966D2DALLASBC",
                "location":"Texas"},
               {"id":"a620baf5-9e7c-429d-81c8-203f8854e5d7",
                "name":"WALMART#22966D2SANFRAN",
                "location":"California"},
               {"id":"edb1e4e0-2e35-4cf3-9404-9efaf26dc982",
                "name":"MOMANDPOP#22966D2BRONX",
                "location":"New York"},
               {"id":"98ca8955-dbcd-4373-832d-8bd492f127ea",
                "name":"DUNKIN-DONUTS#22966D2LONDON",
                "location":"England"}]

    users = [{"user_id":"7fb88da0-2642-4451-835a-26ffc8def3cb",
              "first":"John",
              "last":"Smith",
              "gender":"Male",
              "city":"Seattle",
              "state":"Washington",
              "cc_no":"1234-5678-9123-0432"},
             {"user_id":"5bd7b822-a5e4-485a-9819-7d3ba9ce2bcf",
              "first":"Sally",
              "last":"Smith",
              "gender":"Female",
              "city":"San Francisco",
              "state":"California",
              "cc_no":"2342-3456-9123-2345"},
             {"user_id":"a7b4509a-e676-49db-a7a0-59da5029d214",
              "first":"Adam",
              "last":"Williams",
              "gender":"Male",
              "city":"Austin",
              "state":"Texas",
              "cc_no":"2344-4533-5645-9084"},
             {"user_id":"a7b4509a-e676-49db-a7a0-59da5029d214",
              "first":"Rory",
              "last":"Williams",
              "gender":"Male",
              "city":"Dallas",
              "state":"Texas",
              "cc_no":"5345-4533-2332-2342"},
             {"user_id":"a7b4509a-e676-49db-a7a0-59da5029d214",
              "first":"Amelia",
              "last":"Clark",
              "gender":"Female",
              "city":"New York City",
              "state":"New York",
              "cc_no":"5123-5675-2324-2564"}]

    for merchant in merchants:
        session.execute(insert_merchant.bind(merchant))
        session.execute(set_merchant_counter.bind({"merchant_id":merchant["id"], "total":0, "merchant_name": merchant["name"]}))
    for user in users:
        session.execute(session.prepare("INSERT INTO datastax_creditcard_demo.users (user_id, first, last, gender, city, state, cc_no) VALUES (?,?,?,?,?,?,?)").bind(user))
    while True:

        cc_no_index = randint(0,4)
        cc_no = users[cc_no_index]["cc_no"]
        location = randint(10000,99999)
        transaction_date = time.time()

        merchant = randint(0,3)
        amount = uniform(1.0, 5000.0)
        transaction_id = uuid.uuid1()

        transaction_values = {
            'cc_no': str(cc_no),
            'transaction_id': transaction_id,
            'location': str(location),
            'merchant': merchants[merchant]["name"],
            'amount': amount,
            'status': "",
            'notes': "",
        }
        # transaction_date = datetime.fromtimestamp(time.time()) + timedelta(days=1)
        transaction_by_merchant_date_values = {
            'cc_no': str(cc_no),
            'date': str(transaction_date),
            'transaction_id': transaction_id,
            'merchant': merchants[merchant]["name"],
            'amount': amount,
        }
        increment_trans_counter()
        session.execute(insert_transaction.bind(transaction_values))

        session.execute(insert_transaction_merchant_date.bind(transaction_by_merchant_date_values))
        session.execute(set_merchant_counter.bind({"merchant_id": merchants[merchant]["id"], "total": 1, "merchant_name":merchants[merchant]["name"]}))
        # date = time.time() * 1000
        # for row in QUOTE_DATA:
        #     row['date'] = date
        #     row['current'] = random.uniform(row['low'], row['high'])
        #
        #     session.execute_async(insert_quote.bind(row))
        #     session.execute_async(in1sert_latest.bind(row))
        # print '.'
        time.sleep(1)

def increment_trans_counter():
    global previous_minute
    global previous_hour
    global previous_day

    transaction_counter = session.execute(get_trans_counter)

    tran_time = time
    transaction_datetime = datetime.now()

    if transaction_counter == []:
        session.execute(incr_trans_counter.bind({'date': str(tran_time.time())}))
    else:
        session.execute(incr_trans_counter.bind({'date': transaction_counter[0]['date']}))

    min_transaction_counter = session.execute(get_minute_trans_counter)
    if min_transaction_counter == []:
        session.execute(incr_minute_trans_counter.bind({'date': str(tran_time.time())}))
    elif previous_minute != datetime.now().minute:
        previous_minute = datetime.now().minute
        session.execute(reset_minute_trans_counter.bind({'date': min_transaction_counter[0]['date'], 'total': (int(min_transaction_counter[0]["total"]) * -1) + 1}))
    else:
        session.execute(incr_minute_trans_counter.bind({'date': min_transaction_counter[0]['date']}))

    hour_transaction_counter = session.execute(get_hour_trans_counter)
    if hour_transaction_counter == []:
        session.execute(incr_hour_trans_counter.bind({'date': str(tran_time.time())}))
    elif previous_hour != datetime.now().hour:
        previous_hour = datetime.now().hour
        session.execute(reset_hour_trans_counter.bind({'date': hour_transaction_counter[0]['date'], 'total': (int(hour_transaction_counter[0]["total"]) * -1) + 1}))
    else:
        session.execute(incr_hour_trans_counter.bind({'date': hour_transaction_counter[0]['date']}))

    day_transaction_counter = session.execute(get_day_trans_counter)
    if day_transaction_counter == []:
        session.execute(incr_day_trans_counter.bind({'date': str(tran_time.time())}))
    elif previous_day != datetime.now().day:
        previous_day = datetime.now().day
        session.execute(reset_day_trans_counter.bind({'date': day_transaction_counter[0]['date'], 'total': (int(day_transaction_counter[0]["total"]) * -1) + 1}))
    else:
        session.execute(incr_day_trans_counter.bind({'date': day_transaction_counter[0]['date']}))
stream_quotes()
