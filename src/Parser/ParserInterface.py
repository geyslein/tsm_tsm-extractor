from abc import abstractmethod, ABC

import click

import RawDataSource


class ParserInterface(ABC):

    rawdata_source: RawDataSource.RawDataSourceInterface

    def __init__(self):
        self.datastore = None
        self.rawdata_source = None
        self.progress_bar = click.progressbar(length=0, show_pos=True, label='Parsing raw data')

    def set_datastore(self, datastore):
        self.datastore = datastore

    def set_rawdata_source(self, rawdata_source: RawDataSource.RawDataSourceInterface):
        self.rawdata_source = rawdata_source

    def set_progress_length(self, length: int):
        self.progress_bar.length = length
        # Tune number of updates os only five percent steps are shown
        self.progress_bar.update_min_steps = length / 20

    def update_progress(self, steps=1):
        self.progress_bar.update(steps)

    @abstractmethod
    def do_parse(self):
        raise NotImplementedError

    @abstractmethod
    def load_data(self):
        raise NotImplementedError
