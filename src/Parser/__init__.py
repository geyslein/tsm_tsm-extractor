import Parser
from . import ParserInterface
from .MyCustomParser import MyCustomParser
from .AnotherCustomParser import AnotherCustomParser


def get_parser(parser_type: str) -> ParserInterface:
    # Is this safe as parser_type is user input?
    klass = getattr(Parser, parser_type)
    parser_instance = klass()

    return parser_instance
