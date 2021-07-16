import uuid
from abc import ABC, abstractmethod

from . import Observation


class AbstractDatastore(ABC):

    device_id: uuid.uuid4

    def __init__(self, uri: str, device_id: uuid.uuid4) -> None:
        self.uri: str = uri
        self.device_id: str = device_id
        self.initiate_connection()

    @abstractmethod
    def initiate_connection(self) -> None:
        """Connect to the database or instantiate http classes"""
        raise NotImplementedError

    @abstractmethod
    def store_observations(self, observations: [Observation]) -> None:
        """Save a bunch of observations to the datastore"""
        raise NotImplementedError

    @abstractmethod
    def finalize(self):
        """Do last things to do, e.g. commit to database."""
        raise NotImplementedError
