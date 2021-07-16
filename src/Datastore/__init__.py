import re
import uuid

from .SqlAlchemyDatastore import SqlAlchemyDatastore
from .MqttDatastore import MqttDatastore
from .Observation import Observation
from .AbstractDatastore import AbstractDatastore


def get_datastore(uri: str, device_id: int) -> AbstractDatastore:
    datastore = None

    # Postgres uri
    if re.search('^postgres://', uri):
        datastore = SqlAlchemyDatastore(uri, device_id)

    # Postgresql uri
    if re.search('^postgresql://', uri):
        datastore = SqlAlchemyDatastore(uri, device_id)

    # ORACLE uri
    if re.search('^oracle://', uri):
        datastore = SqlAlchemyDatastore(uri, device_id)

    # MQTT uri
    if re.search('^mqtt://', uri):
        datastore = MqttDatastore(uri, device_id)

    # default
    if datastore is None:
        raise NotImplementedError

    return datastore
