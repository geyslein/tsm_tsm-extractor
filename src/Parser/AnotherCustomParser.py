from datetime import datetime

import click

from Datastore import MqttDatastore, Observation
from Parser.ParserInterface import ParserInterface


class AnotherCustomParser(ParserInterface):

    def load_data(self):
        size = self.rawdata_source.temp_file.tell()
        # @todo check general limits like maximum file size and maximum number of lines or
        #  elements per job

        # Determine the length/number of iterations the parser will do to enable progress reporting
        # Maybe the number of lines in an csv or number of elements in xml raw data
        self.set_progress_length(2000)

    def do_parse(self):

        # For demo only!
        demo_iterations = 200
        # Number of simulated datastreams per iteration
        demp_datastreams = 20

        # override progress length here again only for demo
        self.set_progress_length(demo_iterations*demp_datastreams)

        for n in range(0, demo_iterations):
            ts = datetime.now()
            for i in range(0, demp_datastreams):
                v = Observation(ts, 23, self.rawdata_source.src, i)
                self.datastore.store_observation(v)
                self.update_progress()
