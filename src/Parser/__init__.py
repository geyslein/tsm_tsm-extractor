import Parser
from tsm_datastore_lib import AbstractDatastore
from RawDataSource import AbstractRawDataSource
from .AbstractParser import AbstractParser
from .MyCustomParser import MyCustomParser
from .AnotherCustomParser import AnotherCustomParser
from .CsvParser import CsvParser


def get_parser(
        parser_type: str,
        datasource: AbstractRawDataSource,
        datastore: AbstractDatastore) -> AbstractParser:
    # This is save even if parser_type is user input: It won't throw more then an AttributeError
    klass = getattr(Parser, parser_type)
    parser_instance = klass(datasource, datastore)

    return parser_instance
