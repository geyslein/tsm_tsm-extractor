#!/usr/bin/env python

import logging

import paho.mqtt as mqtt
import paho.mqtt.client


class MqttLoggingHandler(logging.Handler):
    def __init__(self, broker, user, password, topic, client_id="", qos=0, level=logging.NOTSET, **mqtt_kwargs):
        super().__init__(level)
        host = broker.split(":")[0]
        port = int(broker.split(":")[1])
        user = user
        password = password
        client_id = client_id
        
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
        except ConnectionError as e:
            root = logging.getLogger()
            root.removeHandler(self)
            logging.exception(
                f'MQTT logging failed. Disabling MQTT '
                f'logging for current process', exc_info=e
            )

        except Exception:
            self.handleError(record)

    def close(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()
        super().close()
