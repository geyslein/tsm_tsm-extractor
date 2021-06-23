import click

from .DatastoreInterface import DatastoreInterface
from . import Value


class SqlAlchemyDatastore(DatastoreInterface):
    def initiate_connection(self) -> None:
        click.secho(
            'Connecting to sqlalchemy supported database "{}"'.format(self.uri),
            err=True,
            fg="green"
        )

    def store_value(self, value: Value) -> None:
        pass
