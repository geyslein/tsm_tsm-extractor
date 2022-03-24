from abc import abstractmethod, ABC

import click

from tsm_datastore_lib.AbstractDatastore import AbstractDatastore
from RawDataSource import AbstractRawDataSource


class AbstractParser(ABC):

    def __init__(self, rawdata_source: AbstractRawDataSource, datastore: AbstractDatastore):
        self.datastore: AbstractDatastore = datastore
        self.rawdata_source: AbstractRawDataSource = rawdata_source
        self.progress = click.progressbar(length=0, show_pos=True, label='Parsing raw data')
        self.name = self.__class__.__name__

    def set_progress_length(self, length: int):
        self.progress.length = length
        # Tune number of updates so only five percent steps are reported
        self.progress.update_min_steps = length / 20

    def update_progress(self, steps=1):
        self.progress.update(steps)

    @abstractmethod
    def do_parse(self):
        raise NotImplementedError
