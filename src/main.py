from __future__ import annotations
import logging
import os

import click
import tsm_datastore_lib
import Parser
import RawDataSource
import mqtt_logging
from tsm_datastore_lib.AbstractDatastore import AbstractDatastore
from RawDataSource import AbstractRawDataSource


@click.group()
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help="Print more output.",
    envvar='VERBOSE',
    show_envvar=True,
)
def cli(verbose):
    if verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level)


@click.command()
@click.option(
    '-p', '--parser', 'parser_type',
    help='Name of the parser to use to read the raw data. Should be available from `list` command.',
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
    required=True, type=str,
)
@click.option(
    'mqtt_broker', '--mqtt-broker', '-m',
    help="MQTT broker to connect. Explicitly pass 'None' to disable mqtt-logging feature.",
    required=True,
    show_envvar=True,
    envvar='MQTT_BROKER',
)
@click.option(
    'mqtt_user', '--mqtt-user', '-u',
    help='MQTT user',
    show_envvar=True,
    envvar='MQTT_USER'
)
@click.option(
    'mqtt_password', '--mqtt-password', '-pw',
    help='MQTT password',
    show_envvar=True,
    envvar='MQTT_PASSWORD'
)
def parse(parser_type, target_uri, source_uri, device_id, mqtt_broker, mqtt_user, mqtt_password):
    """Parse data of a raw data source to a data store."""

    if mqtt_broker != "None":
        if mqtt_password is None:
            raise click.MissingParameter("mqtt_password", param_type='parameter')
        if mqtt_user is None:
            raise click.MissingParameter("mqtt_user", param_type='parameter')
        mqtt_logging.setup('extractor', mqtt_broker, mqtt_user, mqtt_password, thing_id=device_id)

    logging.info("load datastore")
    datastore = load_datastore(target_uri, device_id)
    logging.info("load source file")
    source = RawDataSource.UrlRawDataSource(source_uri)
    logging.info("load parser")
    parser = load_parser(parser_type, source, datastore)
    logging.info("parsing.. ")
    parser.do_parse()
    datastore.finalize()
    logging.info("parsing.. done")
    logging.info('😁')


def load_datastore(target_uri: str, device_id: int) -> tsm_datastore_lib.AbstractDatastore:
    try:
        datastore = tsm_datastore_lib.get_datastore(target_uri, device_id)
    except NotImplementedError as e:
        msg = f'No matching datastore type for URI pattern "{target_uri}"'
        logging.error(msg)
        raise click.BadParameter(msg)
    return datastore


def load_parser(
        parser_type: str,
        datasource: AbstractRawDataSource, datastore:
        AbstractDatastore
) -> Parser.AbstractParser:
    try:
        parser = Parser.get_parser(parser_type, datasource, datastore)
    except (NotImplementedError, AttributeError) as e:
        msg = f'Bad parser "{parser_type}". Not (completely) implemented yet?'
        logging.error(msg)
        raise click.BadParameter(msg)
    return parser


@click.command()
def version():
    """Display the current version."""
    logging.info(0)


@click.command(name='list')
def list_available():
    """Display available datastore, parser and raw data source types."""
    click.secho('Datastore types', bg='green')
    for n in [cls.__name__ for cls in tsm_datastore_lib.AbstractDatastore.__subclasses__()]:
        click.echo(f'\t{n}')
    click.secho('Parser types', bg='green')
    for n in [cls.__name__ for cls in Parser.AbstractParser.__subclasses__()]:
        click.echo(f'\t{n}')
    click.secho('Raw data source types', bg='green')
    for n in [cls.__name__ for cls in RawDataSource.AbstractRawDataSource.__subclasses__()]:
        click.echo(f'\t{n}')


cli.add_command(parse)
cli.add_command(list_available)
cli.add_command(version)

if __name__ == '__main__':
    cli()
