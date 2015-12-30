create keyspace if not exists datastax_creditcard_demo WITH replication = {
'class': 'NetworkTopologyStrategy',
'DC1': 1,
'Solr': 1
};

use datastax_creditcard_demo; 
 
CREATE TABLE if not exists credit_card_transactions_balance (
	cc_no text,
	transaction_id timeuuid,
	amount double,
	balance_at timestamp static,
	balance double static,
	PRIMARY KEY (cc_no, transaction_id)
) WITH CLUSTERING ORDER BY (transaction_id DESC);

CREATE TABLE if not exists credit_card_transactions_by_merchant_date (
	merchant text,
	date text, 
	transaction_id timeuuid,
	cc_no text,
	amount double,
 	PRIMARY KEY (merchant,cc_no,transaction_id)
) WITH CLUSTERING ORDER BY (cc_no ASC, transaction_id DESC);
	
create table if not exists latest_transactions(
	cc_no text,
	transaction_id timeuuid,
	location text,
	items map<text, double>,
	merchant text,
	amount double,
	status text,
	notes text,
	PRIMARY KEY (cc_no, transaction_id)
) WITH CLUSTERING ORDER BY (transaction_id DESC) 
	 AND compaction= { 'class': 'MemoryOnlyStrategy' }
     AND compression = {'sstable_compression' : ''}
     AND caching = {'keys':'NONE', 'rows_per_partition':'NONE'};

create table if not exists transactions(
	cc_no text,
 	transaction_id timeuuid,
	location text,
	items map<text, double>,
	merchant text,
	amount double,
	status text,
	notes text,
	PRIMARY KEY (transaction_id)
);

create table if not exists blacklist_transactions(
	dummy text,
 	transaction_id timeuuid,
	PRIMARY KEY (transaction_id)
);
     
create table if not exists users(
	user_id text ,
	first text,
	last text,
	gender text,
	city text,
	state text,
	cc_no text,
	PRIMARY KEY (cc_no)
);

create table if not exists merchants(
    id text,
    name text,
    location text,
    PRIMARY KEY (id)
) WITH compaction= { 'class': 'MemoryOnlyStrategy' }
     AND compression = {'sstable_compression' : ''}
     AND caching = {'keys':'NONE', 'rows_per_partition':'NONE'};
    
create table if not exists blacklist_merchants(
	merchant text,
	city text,

	PRIMARY KEY (merchant, city)
) WITH compaction= { 'class': 'MemoryOnlyStrategy' }
     AND compression = {'sstable_compression' : ''}
     AND caching = {'keys':'NONE', 'rows_per_partition':'NONE'};
  	 
	
create table if not exists blacklist_cards(
	dummy text,
	cc_no text,
	amount double,
	PRIMARY KEY (cc_no)
) WITH compaction= { 'class': 'MemoryOnlyStrategy' }
     AND compression = {'sstable_compression' : ''}
     AND caching = {'keys':'NONE', 'rows_per_partition':'NONE'};
  	 
create table if not exists transaction_date_minute_counter (
	date text,
	hour int, 
	minute int,
	total_for_minute counter,
	PRIMARY KEY  (date, hour, minute)
);

create table if not exists trans_merchant_counter (
	merchant_name text,
	merchant_id text,
	total counter,
	PRIMARY KEY  (merchant_id,merchant_name)
);

create table if not exists trans_counter (

	date text,
	total counter,
	PRIMARY KEY  (date)
);
create table if not exists minute_trans_counter (

	date text,
	total counter,
	PRIMARY KEY  (date)
);

create table if not exists hour_trans_counter (

	date text,
	total counter,
	PRIMARY KEY  (date)
);
create table if not exists day_trans_counter (

	date text,
	total counter,
	PRIMARY KEY  (date)
);
//truncate trans_issuer_date_minute_counter;
//truncate trans_user_date_minute_counter;
//truncate blacklist_transactions;
//truncate blacklist_cards;
//truncate blacklist_issuers;
//truncate transactions;
//truncate credit_card_transactions_balance;
//truncate credit_card_transactions_by_issuer_date;
//truncate transaction_date_minute_counter;
//truncate users;

//drop keyspace datastax_creditcard_demo;

