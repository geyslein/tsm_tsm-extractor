from __future__ import annotations

import json
import logging
import os
import warnings

import click
import tsm_datastore_lib
from sqlalchemy.exc import SAWarning

import Parser
import RawDataSource
from RawDataSource import AbstractRawDataSource
from tsm_datastore_lib.AbstractDatastore import AbstractDatastore
import qaqc
import mqtt_logging
import contextlib

import paho.mqtt as mqtt
import paho.mqtt.client


@contextlib.contextmanager
def log_on_error(msg: str, *args, level='error', exc_info=True, stack_info=False, extra=None):
    level = logging.getLevelName(level.upper())
    if isinstance(level, str):
        raise TypeError('level must be integer')
    try:
        yield
    except Exception as e:
        if exc_info is True:
            # hide the 'log_on_error()' call
            e.__traceback__ = e.__traceback__.tb_next
            exc_info = e
        logging.log(level, msg, *args, exc_info=exc_info, stack_info=stack_info, extra=extra)
        raise e


class _DummyClient(mqtt.client.Client):
    """ Same interface as paho.mqtt.client.Client, but does nothing. """
    def __init__(self, *args, **kwargs):
        def f(*a, **kw): pass
        super().__init__(*args, **kwargs)
        for name in dir(self):
            if not name.startswith('_') and callable(getattr(self, name)):
                setattr(self, name, f)


@click.group()
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help="Print more output.",
    envvar='VERBOSE',
    show_envvar=True,
)
def cli(verbose):
    logging.basicConfig(level="DEBUG" if verbose else "INFO")


option_mqtt_broker = click.option(
    'mqtt_broker', '--mqtt-broker', '-m',
    help="MQTT broker to connect. Explicitly pass 'None' to disable "
         "mqtt-logging feature for development.",
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
@option_target_uri
@option_source_uri
@option_device_id
@option_mqtt_broker
@option_mqtt_usr
@option_mqtt_pwd
def parse(parser_type, target_uri, source_uri, device_id, mqtt_broker, mqtt_user,
          mqtt_password):
    """Parse data of a raw data source to a data store."""

    if check_mqtt_params(mqtt_broker, mqtt_user, mqtt_password):
        mqtt_logging.setup('extractor', mqtt_broker, mqtt_user, mqtt_password, device_id)
        client = setup_mqtt_client(mqtt_broker, mqtt_user, mqtt_password)
    else:
        client = _DummyClient()

    with log_on_error(f"Parser: loading datastore failed"):
        datastore = load_datastore(target_uri, device_id)
    with log_on_error(f"Parser: loading source file failed"):
        source = RawDataSource.UrlRawDataSource(source_uri)
    with log_on_error(f"Parser: loading parser failed"):
        parser = load_parser(parser_type, source, datastore)
    with log_on_error(f"Parser: parsing with parser={parser_type!r} failed"):
        parser.do_parse()
        datastore.finalize()
    logging.info("Parser: successfully parsed data")

    # inform the broker, that parsing is done.
    client.publish(
        topic='data_parsed',
        payload=json.dumps(dict(thing_uuid=str(device_id), db_uri=target_uri)),
    )
    client.loop_stop()


@cli.command()
@option_target_uri
@option_device_id
@option_mqtt_broker
@option_mqtt_usr
@option_mqtt_pwd
def run_qaqc(target_uri, device_id, mqtt_broker, mqtt_user, mqtt_password):
    """ Run quality control pipeline on datastore data.

    Loads data and pipeline config from data store. Then run the
    quality control functions defined in the config and write
    the produced quality labels back to the data store
    """
    if check_mqtt_params(mqtt_broker, mqtt_user, mqtt_password):
        mqtt_logging.setup('extractor', mqtt_broker, mqtt_user, mqtt_password, device_id)

    with log_on_error(f"QA/QC: loading datastore failed"):
        datastore = load_datastore(target_uri, device_id)
        logging.info("parse config")
    with log_on_error(f"QA/QC: parsing QA/QC-configuration failed"):
        config = qaqc.parse_qaqc_config(datastore)
    with log_on_error(f"QA/QC: loading data failed"):
        data = qaqc.get_data(datastore, config)
    with log_on_error(f"QA/QC: running QA/QC-configuration on data failed"):
        result = qaqc.run_qaqc_config(data, config)
    with log_on_error(f"QA/QC: uploading quality labels failed"):
        qaqc.upload_qc_labels(result, config, datastore)
    logging.info("QA/QC: successfully run configuration; all quality labels uploaded.")


def check_mqtt_params(mqtt_broker, mqtt_user, mqtt_password):
    if mqtt_broker == "None":
        warnings.warn(
            "Passing 'None' as mqtt_broker is will disable "
            "MQTT logging and will not report to the broker "
            "that parsing is done. Use in development only."
        )
        return False
    if mqtt_password is None:
        raise click.MissingParameter("mqtt_password", param_type='parameter')
    if mqtt_user is None:
        raise click.MissingParameter("mqtt_user", param_type='parameter')
    return True


def setup_mqtt_client(mqtt_broker, mqtt_user, mqtt_password) -> mqtt.client.Client:
    """
    setup client for workflow mqtt-messages, e.g. 'parsing_done'.

    Notes
    -----
    Returned client already was started.
    Call ``client.stop_loop()`` on teardown,
    to ensure all messages was send.
    """
    host = mqtt_broker.split(":")[0]
    port = int(mqtt_broker.split(":")[1])
    client = mqtt.client.Client(f"parser-{os.getpid()}")
    client.username_pw_set(mqtt_user, mqtt_password)
    client.connect(host, port)
    err = client.loop_start()
    if err is not None:
        raise mqtt.MQTTException(mqtt.client.error_string(err))
    return client


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
    warnings.filterwarnings(
        action="ignore",
        category=SAWarning,
        message=r".*TypeDecorator JSONField\(\) will not produce a cache key.*",
    )
    cli()
