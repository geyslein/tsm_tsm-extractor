from abc import abstractmethod, ABC
from tempfile import TemporaryFile


class ParserInterface(ABC):

    def __init__(self):
        self.datastore = None
        self.source_file = None

    def set_datastore(self, datastore):
        self.datastore = datastore

    def set_rawdata_file(self, rawdata_file: TemporaryFile):
        self.source_file = rawdata_file

    @abstractmethod
    def do_parse(self):
        raise NotImplementedError

    @abstractmethod
    def load_data(self):
        raise NotImplementedError
