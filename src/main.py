import click
import Datastore
import Parser
from RawDataSource.HttpRawDataSource import HttpRawDataSource


@click.command()
@click.option(
    '-p', '--parser', 'parser_type',
    help='Name of the parser to use to read the raw data',
    required=True, type=str
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
def parse(parser_type, target_uri, source_uri):

    # Dynamically load the parser
    parser = load_parser(parser_type)
    # Dynamically load the datastore
    datastore = load_datastore(target_uri)
    # Equip the parser with a datastore
    parser.set_datastore(datastore)
    # Load the source file
    source = HttpRawDataSource(source_uri)
    parser.set_rawdata_file(source)
    # Do the parsing work
    parser.do_parse()
    # Return happiness
    click.echo('😁')


def load_datastore(target_uri: str) -> Datastore.DatastoreInterface:
    try:
        datastore = Datastore.get_datastore(target_uri)
    except (NotImplementedError) as e:
        raise click.BadParameter(
            'No matching datastore type for URI pattern "{}".'.format(target_uri)
        )
    return datastore


def load_parser(parser_type: str) -> Parser.ParserInterface:
    try:
        parser = Parser.get_parser(parser_type)
    except (NotImplementedError, AttributeError) as e:
        raise click.BadParameter(
            'Parser "{}" not (completely) implemented yet?'.format(parser_type)
        )
    return parser


@click.group()
def cli():
    pass


cli.add_command(parse)

if __name__ == '__main__':
    cli()
