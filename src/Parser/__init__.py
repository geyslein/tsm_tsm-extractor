import Parser
from Datastore import DatastoreInterface
from RawDataSource import RawDataSourceInterface
from .ParserInterface import ParserInterface
from .MyCustomParser import MyCustomParser
from .AnotherCustomParser import AnotherCustomParser


def get_parser(
        parser_type: str,
        datasource: RawDataSourceInterface,
        datastore: DatastoreInterface) -> ParserInterface:
    # Is this safe as parser_type is user input?
    klass = getattr(Parser, parser_type)
    parser_instance = klass(datasource, datastore)

    return parser_instance
