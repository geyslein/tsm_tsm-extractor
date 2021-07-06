from datetime import datetime

import click

from Datastore import MqttDatastore, Observation
from Parser.ParserInterface import ParserInterface


class AnotherCustomParser(ParserInterface):

    datastore: SqlAlchemyDatastore
    parser_settings: {}

    def __init__(self, rawdata_source: RawDataSourceInterface, datastore: SqlAlchemyDatastore):

        # For demo only!
        self.demo_iterations = 200
        # Number of simulated datastreams per iteration
        self.demo_datastreams = 20
        self.number_of_values = self.demo_iterations*self.demo_datastreams

        super().__init__(rawdata_source, datastore)
        # pick out the parser settings from the datadstores thing when using SqlAlchemyDatastore
        self.parser_settings = self.datastore.get_parser_parameters(self.__class__.__name__)

        # Determine the length/number of iterations the parser will do to enable progress reporting
        # Maybe the number of lines in an csv or number of elements in xml raw data
        self.set_progress_length(2000)

    def do_parse(self):

        # Determine the length/number of iterations the parser will do to enable progress reporting
        # Maybe the number of lines in an csv or number of elements in xml raw data. You already
        # had to calculate this in check_max_elements methode, maybe it's reusable.
        self.set_progress_length(self.number_of_values)

        for n in range(0, self.demo_iterations):
            ts = datetime.now()
            for i in range(0, self.demo_datastreams):
                v = Observation(ts, 23, self.rawdata_source.src, i)
                self.datastore.store_observation(v)
                self.update_progress()
