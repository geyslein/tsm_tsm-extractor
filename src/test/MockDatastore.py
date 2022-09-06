#! /usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List, Dict, Any, Sequence

from tsm_datastore_lib.AbstractDatastore import AbstractDatastore
from tsm_datastore_lib.JournalEntry import JournalEntry
from tsm_datastore_lib.Observation import Observation


class MockDatastore(AbstractDatastore):
    def __init__(self, uri="", device_id="", parser_kwargs=None):
        super().__init__(uri, device_id)
        self.parser_kwargs = parser_kwargs or {}
        self.observations = []
        self.journal_entries = []

    def get_parser_parameters(self, parser_type) -> Dict[str, Any]:
        return self.parser_kwargs

    def initiate_connection(self, schema) -> None:
        return None

    def store_observations(self, observations: List[Observation]) -> None:
        self.observations.extend(observations)

    def store_journal_entries(self, entries: Sequence[JournalEntry]) -> None:
        self.journal_entries.extend(entries)

    def get_observations(self):
        return self.observations

    def finalize(self):
        return None
