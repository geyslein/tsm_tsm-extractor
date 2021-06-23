import re

from .SqlAlchemyDatastore import SqlAlchemyDatastore
from .MqttDatastore import MqttDatastore
from .Value import Value
from .DatastoreInterface import DatastoreInterface


def get_datastore(uri: str) -> DatastoreInterface:
    datastore = None

    # Postgres uri
    if re.search('^postgres://', uri):
        datastore = SqlAlchemyDatastore(uri)

    # ORACLE uri
    if re.search('^oracle://', uri):
        datastore = SqlAlchemyDatastore(uri)

    # MQTT uri
    if re.search('^mqtt://', uri):
        datastore = MqttDatastore(uri)

    # default
    if datastore is None:
        raise NotImplementedError

    return datastore
