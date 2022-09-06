#!/usr/bin/env python
from __future__ import annotations

import json
import os
import logging
import paho.mqtt as mqtt
import paho.mqtt.client


class MqttLoggingHandler(logging.Handler):
    def __init__(
        self,
        broker,
        user,
        password,
        topic,
        client_id="",
        qos=0,
        level=logging.NOTSET,
    ):
        super().__init__(level)
        host = broker.split(":")[0]
        port = int(broker.split(":")[1])
        user = user
        password = password
        client_id = client_id

        self.name = client_id
        self.topic = topic
        self.qos = qos
        self.client = mqtt.client.Client(client_id)
        self.client.username_pw_set(user, password)
        self.client.connect(host, port)

        err = self.client.loop_start()
        if err is not None:
            raise mqtt.MQTTException(mqtt.client.error_string(err))

    def emit(self, record: logging.LogRecord) -> None:
        # todo document the qos feature
        try:
            self.client.publish(
                topic=self.topic,
                payload=self.format(record),
                qos=record.qos if hasattr(record, "qos") else self.qos,
            )
        except Exception:
            self.handleError(record)

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            dict(
                timestamp=record.created,
                level=record.levelname,
                message=record.message,
                extra=dict(
                    filename=record.filename,
                    pid=record.process,
                ),
            )
        )

    def close(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()
        super().close()


def setup(
    name: str,
    mqtt_broker: str,
    mqtt_user: str,
    mqtt_password: str,
    thing_id: str,
    level: int | str | None = None,
):
    """
    Set up the MQTT logging

    Parameters
    ----------
    name : str
        The name that will appear as the source of log messages

    mqtt_broker : str
        The broker to send to in the form: `URI:PORT`

    mqtt_user : str
        Username to register with the broker

    mqtt_password : str
        Password to register with the broker

    thing_id : str
        The ID of the thing the log messages belong to. This also
        determines the mqtt topic, which will set to `logging/THING_ID`.

    level : str, int or None, default None
        The logging level. Iff `None` the level will be the same as
        the root-logger of the logging module.

    Returns
    -------
    None
    """
    root = logging.getLogger()
    name = f"{name}-{os.getpid()}"

    if level is None:
        level = root.level

    # prevent to add same handler multiple times
    for h in root.handlers:
        if h.name == name:
            return

    try:
        handler = MqttLoggingHandler(
            mqtt_broker,
            mqtt_user,
            mqtt_password,
            topic=f"logging/{thing_id}",
            client_id=name,
            level=level,
        )
    except ConnectionRefusedError as e:
        raise type(e)(*e.args, "MQTT-Broker down ?") from None

    root.addHandler(handler)

