from abc import ABC, abstractmethod

from . import Value


class DatastoreInterface(ABC):

    def __init__(self, uri: str) -> None:
        self.uri = uri
        self.initiate_connection()

    @abstractmethod
    def initiate_connection(self) -> None:
        """Connect to the databse or instantiate http classes"""
        raise NotImplementedError

    def store_value(self, value: Value) -> None:
        """Save a new value to the datastore"""
        raise NotImplementedError
