import click

from .DatastoreInterface import DatastoreInterface
from . import Observation


class MqttDatastore(DatastoreInterface):
    def initiate_connection(self) -> None:
        click.secho(
            'Setup MQTT datastore connection to "{}"'.format(self.uri),
            err=True,
            fg="green"
        )

    def store_observation(self, observation: Observation) -> None:
        pass
