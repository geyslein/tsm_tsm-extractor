#!/usr/bin/env python

import logging
import paho.mqtt.publish as publish


class MqttLoggingHandler(logging.Handler):
    def __init__(
        self,
        broker,
        port,
        user,
        password,
        level=logging.NOTSET,
        topic="logging",
        client_id="",
        qos=0,
        **mqtt_kwargs
    ):
        super().__init__(level)
        self.topic = topic
        self.broker = broker
        self.user = user
        self.password = password
        self.port = port
        self.client_id = client_id
        self.qos = qos
        self._mqtt_kwargs = mqtt_kwargs

    def emit(self, record: logging.LogRecord) -> None:
        # todo document the qos feature
        if hasattr(record, "qos"):
            qos = record.qos
        else:
            qos = self.qos
        try:
            publish.single(
                topic=self.topic,
                payload=self.format(record),
                qos=qos,
                hostname=self.broker,
                port=self.port,
                client_id=self.client_id,
                auth={
                    "username": self.user,
                    "password": self.password,
                },
            )
        except Exception:
            self.handleError(record)
