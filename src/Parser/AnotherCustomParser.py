from datetime import datetime

import click

from Datastore import MqttDatastore, Observation
from Parser.ParserInterface import ParserInterface


class AnotherCustomParser(ParserInterface):

    def __init__(self):
        super().__init__()
        self.total = 100
        self.current = 0

    def report_progress(self):
        return self.current / self.total

    def load_data(self):
        size = self.rawdata_source.temp_file.tell()
        click.echo('Size of source file: {}'.format(size))

    def do_parse(self):

        with click.progressbar(length=10000,
                               label='Parsing raw data') as bar:

            for n in range(0, 500):
                ts = datetime.now()
                for i in range(0, 20):
                    v = Observation(ts, 23, "Mars", i)
                    self.datastore.store_observation(v)
                    bar.update(1)
