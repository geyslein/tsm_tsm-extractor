import uuid
from abc import ABC, abstractmethod

from . import Observation


class DatastoreInterface(ABC):

    device_id: uuid.uuid4

    def __init__(self, uri: str, device_id: uuid.uuid4) -> None:
        self.uri = uri
        self.device_id = device_id
        self.initiate_connection()

    @abstractmethod
    def initiate_connection(self) -> None:
        """Connect to the databse or instantiate http classes"""
        raise NotImplementedError

    @abstractmethod
    def store_observation(self, observation: Observation) -> None:
        """Save a new value to the datastore"""
        raise NotImplementedError

    @abstractmethod
    def store_observations(self, observations: [Observation]) -> None:
        """Save a bunch of observations to the datastore"""
        raise NotImplementedError

    @abstractmethod
    def finalize(self):
        """Do last things to do, e.g. commit to database."""
        raise NotImplementedError
