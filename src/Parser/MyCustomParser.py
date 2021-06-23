import click
import Datastore
# import numpy as np
from datetime import datetime
from Parser.ParserInterface import ParserInterface


class MyCustomParser(ParserInterface):

    def do_parse(self):

        # your custom numpy magic
        # dataset = np.loadtxt('path', dtype=np.str, delimiter=',')  # Read file
        dataset = [{
            "datetime": datetime.now(),
            "value": 23,
            "origin": "todo - get from load_data?",
            "position": 42
        }]

        for item in dataset:
            v = Datastore.Value(item["datetime"], item["value"], item["origin"], item["position"])
            self.datastore.store_value(v)

    def load_data(self):
        click.echo('Load data from somewhere')
