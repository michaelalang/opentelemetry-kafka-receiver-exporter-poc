# OpenTelemetry Colletor with Kafka receivers and exporters

This small POC is for show-casing how Kafka can be integrated with OpenTelemetry collector in both ways:

* Receiving, meaning subscribing to a Broker and topic (default otlp_logs)
* Exporting, meaning publishing to a Broker and topic

## requirements and setup

* python3
* pip requirements as defined in `requirementes.txt` 
* podman 
* access to the Red Hat registry or docker.io

### setting up python to for Kafka producer and consumer

* select the OpenTelemetry Collector image based upon your access to the registry

    * for Red Hat Built of OpenTelemetry image execute following command

        ```
        export IMAGE=registry.redhat.io/rhosdt/opentelemetry-collector-rhel8@sha256:7c17ab8dcbc458f9a194a8d9a1adda1c8142ba06f9572ee3713021edf1a8a0ad
        ```

    * for the Community OpenTelemetry image on Docker.io execute following command

        ```
        export IMAGE=docker.io/otel/opentelemetry-collector-contrib:latest
        ```

* to install the required packages for the POC execute the following command

```
pip install -r requirements.txt
```

* to run a Kafka broker in a container listening on port `9092` execute the following command

```
podman run -d --rm -p 9092:9092 --name broker apache/kafka:latest
```

* to run an OpenTelemtry Collector in a container execute the following commands

    * change the SELinux context of the OTEL Collector configuration by executing following commmand
        ```
        sudo chcon -t container_file_t collector.yml
        ```

    * run the OpenTelemetry Collector Container by executing following command
        ```
        podman run --rm --replace -d --net=host --name otel \
          -v $(pwd)/collector.yml:/config/collector.yml \
          ${IMAGE} \
          --config=/config/collector.yml
        ```

* **NOTE** you require the parameter `--net=host` since the POC is loopback(127.0.0.1) based

## Use cases 

### Use case 1

In this use case, the Producer will create one message to the broker into the `otlp_logs` channel.
The OTEL collector will receive the message from the broker, decode the body to an ascii string representation
and use the debug exporter to print the content to the stdout of the container

* the consumer is not expected to receive the message from the broker
* to verify if the Kafka consumer does not receive the message executing following command

```
./consumer.py &
```

* to create a Kafka message execute following command
```
./producer
```

* to see the OTEL collector debug exporter output execute following command

```
podman logs otel 2>&1  |grep Body -B11 -A4
```

* example output

```
--
2025-08-06T17:11:45.195Z	info	Logs	{"kind": "exporter", "data_type": "logs", "name": "debug", "resource logs": 1, "log records": 1}
2025-08-06T17:11:45.195Z	info	ResourceLog #0
Resource SchemaURL: 
ScopeLogs #0
ScopeLogs SchemaURL: 
InstrumentationScope  
LogRecord #0
ObservedTimestamp: 1970-01-01 00:00:00 +0000 UTC
Timestamp: 1970-01-01 00:00:00 +0000 UTC
SeverityText: 
SeverityNumber: Unspecified(0)
Body: Str({"message": "Field lay move tonight draw. Avoid seek under center. Space too voice it be organization feeling door. Ability land explain stuff wear just free.", "host": "oteltest", "facility": "user", "hostname": "oteltest", "application": "__main__", "service_name": "otel", "service_namespace": "otel-test", "timestamp": 1754500305.0182943, "level": "INFO", "pid": 1635428})
Trace ID: 
Span ID: 
Flags: 0
	{"kind": "exporter", "data_type": "logs", "name": "debug"}
```

* there should not be any message being printed by the consumer 

### Use case 2

In this use case, the Producer will create one message to the broker into the `otlp_logs` channel.
With the adjustments made in the following steps, the OTEL collector will in addition to use case 1 also transform 
the message body to JSON and further assign the attributes from JSON as well to the loki attribute keys.

* Edit the `collector.yml` file uncommenting the `logs/kafka/json` Pipeline with it's receivers,processors and exporters as follows

```
service:
  telemetry:
    logs:
      level: "debug"
  pipelines:
    logs/kafka/simple:
      receivers: 
        - kafka
      processors: 
        - memory_limiter
        - transform/kafka
        - batch
      exporters: 
        - debug
    logs/kafka/json:
      receivers:
        - kafka
      processors: 
        - memory_limiter
        - transform/kafka/json
        - attributes/loki
        - batch
      exporters: 
        - debug
        - kafka/exporter/logs2
        - kafka/exporter/logs3
```

* Restart the OTEL collector container by executing following command

```
podman run --rm --replace -d --net=host --name otel \
  -v $(pwd)/collector.yml:/config/collector.yml \
  docker.io/otel/opentelemetry-collector-contrib:latest \
  --config=/config/collector.yml
```

* to create a Kafka message execute following command
```
./producer
```

* the consumer should have been printing the created message as the OTEL collector forwards it to the approriate topic with this configuration

```
ConsumerRecord(topic='otlp_logs2', partition=0, leader_epoch=0, offset=7, timestamp=1754503531351, timestamp_type=0, key=None, value=b'{"application":"__main__","facility":"user","host":"oteltest","hostname":"oteltest","level":"INFO","message":"Necessary tonight decade upon reality green.","pid":1637007,"service_name":"otel","service_namespace":"otel-test","timestamp":1754503531.0635996}', headers=[], checksum=None, serialized_key_size=-1, serialized_value_size=255, serialized_header_size=-1)
```

* to see the OTEL collector debug exporter output execute following command

```
podman logs otel 2>&1  |grep Attributes -B12 -A16
```

* example output

```
	{"kind": "exporter", "data_type": "logs", "name": "debug"}
2025-08-06T17:20:48.500Z	info	ResourceLog #0
Resource SchemaURL: 
ScopeLogs #0
ScopeLogs SchemaURL: 
InstrumentationScope  
LogRecord #0
ObservedTimestamp: 1970-01-01 00:00:00 +0000 UTC
Timestamp: 1970-01-01 00:00:00 +0000 UTC
SeverityText: 
SeverityNumber: Unspecified(0)
Body: Map({"application":"__main__","facility":"user","host":"oteltest","hostname":"oteltest","level":"INFO","message":"Assume agency return ready. Under yard analysis. Situation Mr relationship indicate political.","pid":1635777,"service_name":"otel","service_namespace":"otel-test","timestamp":1754500848.2008853})
Attributes:
     -> message: Str(Assume agency return ready. Under yard analysis. Situation Mr relationship indicate political.)
     -> host: Str(oteltest)
     -> service_name: Str(otel)
     -> pid: Double(1635777)
     -> timestamp: Double(1754500848.2008853)
     -> level: Str(INFO)
     -> facility: Str(user)
     -> hostname: Str(oteltest)
     -> application: Str(__main__)
     -> service_namespace: Str(otel-test)
     -> loki.attribute.labels: Str(service_name, service_namespace, application, hostname, host, level, facility, connection_hostname, trace_id, span_id, trace_flags)
     -> loki.format: Str(raw)
Trace ID: 
Span ID: 
Flags: 0
	{"kind": "exporter", "data_type": "logs", "name": "debug"}
```

* the collcetor output show that we have been successfully parsing the Kakfa message from from JSON to Attributes

* stop the consumer by executing following command

```
kill %1
```

* example output
```
[1]+  Terminated              ./consumer.py
```

* restart the consumer and subscribe to the topic `otel_logs3` by executing following command
```
./consumer otlp_logs3 & 
```

* create another message with the producer by executing following command

```
./producer
```

* the consumer should have been printing the `otlp_logs3` channel message received
* example output

```
ConsumerRecord(topic='otlp_logs3', partition=0, leader_epoch=0, offset=4, timestamp=1754503897388, timestamp_type=0, key=None, value=b'{"application":"__main__","facility":"user","host":"oteltest","hostname":"oteltest","level":"INFO","message":"American nation issue against score work.","pid":1637187,"service_name":"otel","service_namespace":"otel-test","timestamp":1754503897.2416725}', headers=[], checksum=None, serialized_key_size=-1, serialized_value_size=252, serialized_header_size=-1)
```

* stop the consumer by executing following command

```
kill %1
```

* stop and remove the OTEL collector container by executing following command

```
podman rm -f otel
```

* stop and remove the Kafka Broker container by executing following command

```
podman rm -f broker
```
