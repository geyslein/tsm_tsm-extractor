import click

from .AbstractDatastore import AbstractDatastore
from . import Observation


class MqttDatastore(AbstractDatastore):
    def initiate_connection(self) -> None:
        click.secho(
            'Setup MQTT datastore connection to "{}"'.format(self.uri),
            err=True,
            fg="green"
        )

    def store_observation(self, observation: Observation) -> None:
        pass

    def store_observations(self, observations: [Observation]) -> None:
        raise NotImplementedError
