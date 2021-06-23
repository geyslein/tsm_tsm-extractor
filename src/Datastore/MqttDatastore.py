import click

from .DatastoreInterface import DatastoreInterface
from . import Value


class MqttDatastore(DatastoreInterface):
    def initiate_connection(self) -> None:
        click.secho(
            'Setup MQTT datastore connection to "{}"'.format(self.uri),
            err=True,
            fg="green"
        )

    def store_value(self, value: Value) -> None:
        pass
