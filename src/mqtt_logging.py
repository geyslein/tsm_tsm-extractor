#!/usr/bin/env python

import logging
import warnings

import paho.mqtt.publish as publish


class MqttLoggingHandler(logging.Handler):
    def __init__(self, broker, user, password, topic, client_id="", qos=0, level=logging.NOTSET, **mqtt_kwargs):
        super().__init__(level)
        self.host = broker.split(":")[0]
        self.port = int(broker.split(":")[1])
        self.user = user
        self.password = password
        self.topic = topic
        self.client_id = client_id
        self.qos = qos
        self.mqtt_kwargs = mqtt_kwargs

    def emit(self, record: logging.LogRecord) -> None:
        # todo document the qos feature
        try:
            publish.single(
                topic=self.topic,
                payload=self.format(record),
                qos=record.qos if hasattr(record, "qos") else self.qos,
                hostname=self.host,
                port=self.port,
                client_id=self.client_id,
                auth={
                    "username": self.user,
                    "password": self.password,
                },
                **self.mqtt_kwargs
            )
        except Exception:
            self.handleError(record)
