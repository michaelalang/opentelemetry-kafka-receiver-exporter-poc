#!/usr/bin/python

from kafka import KafkaConsumer
import sys
try:
    topic = sys.argv[1]
except IndexError:
    topic = 'otlp_logs2'
consumer = KafkaConsumer(topic)
try:
    for msg in consumer:
        print (msg)
except KeyboardInterrupt:
    print(f"shutting down")
