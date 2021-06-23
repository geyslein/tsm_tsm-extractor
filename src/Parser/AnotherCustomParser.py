from datetime import datetime

from Datastore import MqttDatastore, Value
from Parser.ParserInterface import ParserInterface


class AnotherCustomParser(ParserInterface):
    def load_data(self):
        pass

    def do_parse(self):
        v = Value(datetime.now(), 23, "Mars", 42)
        self.datastore.store_value(v)
