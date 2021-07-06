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
        self.progress_bar = click.progressbar(length=0, show_pos=True, label='Parsing raw data')
        self.check_max_elements()

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
    def check_max_elements(self):
        """Check for the maximum number of elements, for example number of rows times number of
        columns in a csv file or number of xml elements."""
        raise NotImplementedError


class MaximumNumberOfElementsError(Exception):
    def __init__(self, number_of_values):
        self.number_of_values = number_of_values
        self.message = 'Maximum number of elements ({}) exceeded.' \
                       'Current number of elements: {}'.format(MAX_ELEMENTS, number_of_values)
        super().__init__(self.message)
