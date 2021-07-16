import uuid

import click
import Datastore
import Parser
import RawDataSource
from Datastore import AbstractDatastore
from RawDataSource import AbstractRawDataSource


@click.command()
@click.option(
    '-p', '--parser', 'parser_type',
    help='Name of the parser to use to read the raw data',
    required=True, type=str
)
@click.option(
    '-d', '--device-id', 'device_id',
    help='UUID of the device (or "thing") which generated the raw data',
    required=True, type=click.UUID
)
@click.option(
    '-t', '--target-uri', 'target_uri',
    help='URI of the datastore where the parsed data should be written. Example: '
         'postgres://user:password@example.com:5432/mydatabase',
    required=True, type=str
)
@click.option(
    '-s', '--source', 'source_uri',
    help='URI of the raw data file to parse. Example: '
         'https://example.com/minio/f8964b34-d38f-11eb-adae-125e5a40a845',
    required=True, type=str
)
def parse(parser_type, target_uri, source_uri, device_id):
    """Parse data of a raw data source to a data store."""
    # Dynamically load the datastore
    datastore = load_datastore(target_uri, device_id)
    # Load the source file
    source = RawDataSource.HttpRawDataSource(source_uri)
    # Dynamically load the parser
    parser = load_parser(parser_type, source, datastore)
    # Do the parsing work
    parser.do_parse()
    # Finalize the datastore connections
    datastore.finalize()
    # Return happiness
    click.echo('😁')


def load_datastore(target_uri: str, device_id: int) -> Datastore.AbstractDatastore:
    try:
        datastore = Datastore.get_datastore(target_uri, device_id)
    except (NotImplementedError) as e:
        raise click.BadParameter(
            'No matching datastore type for URI pattern "{}".'.format(target_uri)
        )
    return datastore


def load_parser(
        parser_type: str,
        datasource: AbstractRawDataSource, datastore:
        AbstractDatastore) -> Parser.AbstractParser:
    try:
        parser = Parser.get_parser(parser_type, datasource, datastore)
    except (NotImplementedError, AttributeError) as e:
        raise click.BadParameter(
            'Parser "{}" not (completely) implemented yet?'.format(parser_type)
        )
    return parser


@click.command()
def version():
    """Display the current version."""
    click.echo(0)


@click.command(name='list')
def list_available():
    """Display available datastore, parser and raw data source types."""
    click.secho('Datastore types', bg='green')
    for n in [cls.__name__ for cls in Datastore.AbstractDatastore.__subclasses__()]:
        click.echo('\t{}'.format(n))
    click.secho('Parser types', bg='green')
    for n in [cls.__name__ for cls in Parser.AbstractParser.__subclasses__()]:
        click.echo('\t{}'.format(n))
    click.secho('Raw data source types', bg='green')
    for n in [cls.__name__ for cls in RawDataSource.AbstractRawDataSource.__subclasses__()]:
        click.echo('\t{}'.format(n))


@click.group()
def cli():
    pass


cli.add_command(parse)
cli.add_command(list_available)
cli.add_command(version)

if __name__ == '__main__':
    cli()
