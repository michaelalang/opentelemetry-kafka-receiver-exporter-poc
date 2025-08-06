#!/usr/bin/python

from faker import Faker
import json, time, os
from kafka import KafkaProducer
factory = Faker()
producer = KafkaProducer(bootstrap_servers='localhost:9092')
for _ in range(1):
    producer.send('otlp_logs', json.dumps({"message":factory.paragraph(), 
                                           "host": "oteltest", 
                                           "facility": "user", 
                                           "hostname": "oteltest", 
                                           "application": "otel-testing", 
                                           "service_name": "otel", 
                                           "service_namespace": "otel-test", 
                                           "timestamp": time.time(), 
                                           "level": "INFO", 
                                           "pid": os.getpid(), 
                                           "application": __name__}).encode('utf8'))
producer.flush()
