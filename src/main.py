from __future__ import annotations
import logging
import os

import click
import tsm_datastore_lib
import Parser
import RawDataSource
from RawDataSource import AbstractRawDataSource
from tsm_datastore_lib.AbstractDatastore import AbstractDatastore
import qcqa
import mqtt_logging


@click.group()
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help="Print more output.",
    envvar='VERBOSE',
    show_envvar=True,
)
@click.pass_context
def cli(verbose):
    if verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level)


option_mqtt_broker = click.option(
    'mqtt_broker', '--mqtt-broker', '-m',
    help="MQTT broker to connect. Explicitly pass 'None' to disable mqtt-logging feature.",
    required=True,
    show_envvar=True,
    envvar='MQTT_BROKER',
)
option_mqtt_usr = click.option(
    'mqtt_user', '--mqtt-user', '-u',
    help='MQTT user',
    show_envvar=True,
    envvar='MQTT_USER'
)
option_mqtt_pwd = click.option(
    'mqtt_password', '--mqtt-password', '-pw',
    help='MQTT password',
    show_envvar=True,
    envvar='MQTT_PASSWORD'
)
option_device_id = click.option(
    '-d', '--device-id', 'device_id',
    help='UUID of the device (or "thing") which generated the raw data',
    required=True, type=click.UUID
)
option_target_uri = click.option(
    '-t', '--target-uri', 'target_uri',
    help='URI of the datastore where the parsed data should be written. Example: '
         'postgres://user:password@example.com:5432/mydatabase',
    required=True, type=str
)
option_source_uri = click.option(
    '-s', '--source', 'source_uri',
    help='URI of the raw data file to parse. Example: '
         'https://example.com/minio/f8964b34-d38f-11eb-adae-125e5a40a845',
    required=True, type=str,
)


@cli.command()
@click.option(
    '-p', '--parser', 'parser_type',
    help='Name of the parser to use to read the raw data. Should be available from `list` command.',
    required=True, type=str
)
@option_device_id
@option_target_uri
@option_source_uri
@option_mqtt_broker
@option_mqtt_usr
@option_mqtt_pwd
def parse(parser_type, target_uri, source_uri, device_id, mqtt_broker, mqtt_user,
          mqtt_password):
    """Parse data of a raw data source to a data store."""

    setup_mqtt(mqtt_broker, mqtt_user, mqtt_password, device_id)

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


@cli.command()
@option_target_uri
@option_device_id
@option_mqtt_broker
@option_mqtt_usr
@option_mqtt_pwd
def run_qcqa(target_uri, device_id, mqtt_broker, mqtt_user, mqtt_password):
    """ Run quality control pipeline on datastore data.

    Loads data and pipeline config from data store. Then run the
    quality control functions defined in the config and write
    the produced quality labels back to the data store
    """
    setup_mqtt(mqtt_broker, mqtt_user, mqtt_password, device_id)
    datastore = load_datastore(target_uri, device_id)
    config = qcqa.parse_qcqa_config(datastore)
    data = qcqa.get_data(datastore, config)
    result = qcqa.run_qcqa_config(data, config)


def setup_mqtt(mqtt_broker, mqtt_user, mqtt_password, device_id):
    if mqtt_broker != "None":
        if mqtt_password is None:
            raise click.MissingParameter("mqtt_password", param_type='parameter')
        if mqtt_user is None:
            raise click.MissingParameter("mqtt_user", param_type='parameter')
        mqtt_logging.setup('extractor', mqtt_broker, mqtt_user, mqtt_password,
                           thing_id=device_id)


def load_datastore(target_uri: str,
                   device_id: int) -> tsm_datastore_lib.AbstractDatastore:
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


@cli.command()
def version():
    """Display the current version."""
    logging.info(0)


@cli.command(name='list')
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


if __name__ == '__main__':
    cli()
