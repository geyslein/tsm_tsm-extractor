from abc import abstractmethod, ABC
from tempfile import TemporaryFile

import RawDataSource


class ParserInterface(ABC):

    rawdata_source: RawDataSource.RawDataSourceInterface

    def __init__(self):
        self.datastore = None
        self.rawdata_source = None

    def set_datastore(self, datastore):
        self.datastore = datastore

    def set_rawdata_source(self, rawdata_source: RawDataSource.RawDataSourceInterface):
        self.rawdata_source = rawdata_source

    @abstractmethod
    def report_progress(self):
        raise NotImplementedError

    @abstractmethod
    def do_parse(self):
        raise NotImplementedError

    @abstractmethod
    def load_data(self):
        raise NotImplementedError
