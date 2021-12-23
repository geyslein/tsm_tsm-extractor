#! /usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List, Dict, Any

from Datastore.AbstractDatastore import AbstractDatastore
from Datastore.Observation import Observation


class MockDatastore(AbstractDatastore):
    def __init__(self, uri, device_id, parser_kwargs):
        super().__init__(uri, device_id)
        self.parser_kwargs = parser_kwargs
        self.observations = []

    def get_parser_parameters(self, parser_type) -> Dict[str, Any]:
        return self.parser_kwargs

    def initiate_connection(self) -> None:
        return None

    def store_observations(self, observations: List[Observation]) -> None:
        self.observations.extend(observations)

    def get_observations(self):
        return self.observations

    def finalize(self):
        return None
