import Parser
from Datastore import AbstractDatastore
from RawDataSource import AbstractRawDataSource
from .AbstractParser import AbstractParser
from .MyCustomParser import MyCustomParser
from .AnotherCustomParser import AnotherCustomParser


def get_parser(
        parser_type: str,
        datasource: AbstractRawDataSource,
        datastore: AbstractDatastore) -> AbstractParser:
    # Is this safe as parser_type is user input?
    klass = getattr(Parser, parser_type)
    parser_instance = klass(datasource, datastore)

    return parser_instance
