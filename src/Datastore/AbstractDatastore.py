from typing import Sequence, Dict, Any

import uuid
from abc import ABC, abstractmethod

from .Observation import Observation


class AbstractDatastore(ABC):

    def __init__(self, uri: str, device_id: uuid.UUID) -> None:
        self.uri: str = uri
        self.device_id: uuid.UUID = device_id
        self.initiate_connection()

    @abstractmethod
    def get_parser_parameters(self, parser_type) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def initiate_connection(self) -> None:
        """Connect to the database or instantiate http classes"""
        raise NotImplementedError

    @abstractmethod
    def store_observations(self, observations: Sequence[Observation]) -> None:
        """Save a bunch of observations to the datastore"""
        raise NotImplementedError

    @abstractmethod
    def finalize(self):
        """Do last things to do, e.g. commit to database."""
        raise NotImplementedError
