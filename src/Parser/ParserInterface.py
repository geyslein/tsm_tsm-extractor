from abc import abstractmethod, ABC

import click

import RawDataSource
from Datastore import DatastoreInterface
from RawDataSource import RawDataSourceInterface

MAX_ELEMENTS = 100000


class ParserInterface(ABC):

    rawdata_source: RawDataSource.RawDataSourceInterface

    def __init__(self, rawdata_source: RawDataSourceInterface, datastore: DatastoreInterface):
        self.datastore = datastore
        self.rawdata_source = rawdata_source

    def set_progress_length(self, length: int):
        self.progress_bar.length = length
        # Tune number of updates so only five percent steps are reported
        self.progress_bar.update_min_steps = length / 20

    def update_progress(self, steps=1):
        self.progress_bar.update(steps)

    @abstractmethod
    def do_parse(self):
        raise NotImplementedError

    @abstractmethod
    def load_data(self):
        raise NotImplementedError
