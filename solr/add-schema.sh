#!/bin/bash
set -v
KEYSPACE=ticker

if [ "$1" == "-r" ] ; then
    ACTION=RELOAD
    shift
else
    ACTION=CREATE
fi

TABLE=$1
   
echo "Posting solrconfig ..."
curl --data-binary @solrconfig.xml -H 'Content-type:text/xml; charset=utf-8' "http://localhost:8983/solr/resource/ticker.latest/solrconfig.xml"

echo "Posting schema ..."
curl --data-binary ticker.xml -H 'Content-type:text/xml; charset=utf-8' "http://localhost:8983/solr/resource/ticker.latest/schema.xml" 

echo "Creating index..."
curl  -H 'Content-type:text/xml; charset=utf-8' -X POST "http://localhost:8983/solr/admin/cores?action=$ACTION&name=ticker.latest"
echo "Created index."

