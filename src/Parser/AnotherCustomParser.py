from datetime import datetime
from Datastore import Observation, SqlAlchemyDatastore
from Parser.AbstractParser import AbstractParser
from RawDataSource import AbstractRawDataSource


class AnotherCustomParser(AbstractParser):

    def __init__(self, rawdata_source: AbstractRawDataSource, datastore: SqlAlchemyDatastore):

        # Type hints for PyCharm
        self.datastore: SqlAlchemyDatastore
        self.parser_settings: {}

        # For demo only!
        self.demo_iterations = 2
        # Number of simulated datastreams per iteration
        self.demo_datastreams = 20
        self.number_of_values = self.demo_iterations * self.demo_datastreams

        super().__init__(rawdata_source, datastore)
        # pick out the parser settings from the datadstores thing when using SqlAlchemyDatastore
        self.parser_settings = self.datastore.get_parser_parameters(self.__class__.__name__)

    def do_parse(self):

        # Type hints for PyCharm
        self.datastore: SqlAlchemyDatastore

        # Determine the length/number of iterations the parser will do to enable progress reporting
        # Maybe the number of lines in an csv or number of elements in xml raw data.
        self.set_progress_length(self.number_of_values)

        for n in range(0, self.demo_iterations):
            ts = datetime.now()
            for i in range(0, self.demo_datastreams):
                v = Observation(ts, 23, self.rawdata_source.src, i)
                self.datastore.store_observations([v])
                self.update_progress()
