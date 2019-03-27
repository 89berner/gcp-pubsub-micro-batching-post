#!/bin/bash

/opt/logstash/bin/logstash -f /opt/conf/logstash.conf &
echo "Give some time for logstash to start..";
sleep 60;
python3 /indexer/indexer.py
