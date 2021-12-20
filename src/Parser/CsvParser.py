#! /usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Dict, Iterator, List
from io import BytesIO

import numpy as np
import pandas as pd
from Datastore.AbstractDatastore import AbstractDatastore

from Datastore.Observation import Observation, NanNotAllowedHereError
from Datastore.SqlAlchemyDatastore import SqlAlchemyDatastore
from Parser.AbstractParser import AbstractParser
from RawDataSource.AbstractRawDataSource import AbstractRawDataSource

"""
A basic CSV-Parser.

NOTE:
The actual file reading and most `parser_parameters` are directly redirected to
the external function `pandas.read_csv`. Some of the parameters are renamed,
however (by the time of this writing `timestamp_format`, `timestamp_column`, but YMMV),
mainly for reasons of consistency with the domain vocabulary.

All currently supported parser arguments are listed in the module global variables
`REQUIRED_SETTINGS` and `DEFAULT_SETTINGS`, to extend the set of parameters, add
elements to those data structures.

For a detailed description of all available parameters and their semantics, please
refer to the pandas documentation:
https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
"""

# Need to be given in `AbstractDatastore.get_parser_parameters`
REQUIRED_SETTINGS = {
    "delimiter",  # column seperator
    "header",  # number of header lines
    "timestamp_column",  # 0-based index of the date column, will be mapped to `index_column`
    "timestamp_format",  # date format string as described in: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior.
}


# Optional arguments. If a `key` is not given in `AbstractDatastore.get_parser_parameters`,
# the respective `value` is passed to `pandas.read_csv`
DEFAULT_SETTINGS = {
    "comment": "#",
    "decimal": ".",
    "na_values": None,
    "encoding": "utf-8",
    "skipfooter": 0,
    "engine": "python",
}


class CsvParser(AbstractParser):
    def __init__(
        self, rawdata_source: AbstractRawDataSource, datastore: AbstractDatastore
    ):
        super().__init__(rawdata_source, datastore)

    @staticmethod
    def _prep_parser_kwargs(parser_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check the given parser parameters for completeness and correctness,
        add all missing `DEFAULT_ARGUMENTS`

        Parameters
        ----------
        parser_kwargs:
            parser parameters, will be 'translated' if necessary and passed to
            `pandas.read_csv`

        Returns
        -------
        parser parameters
        """
        keys = set(parser_kwargs.keys())
        if diff := REQUIRED_SETTINGS - keys:
            raise TypeError(f"missing required argument(s): {diff}")
        if diff := keys - REQUIRED_SETTINGS - DEFAULT_SETTINGS.keys():
            raise TypeError(f"invalid argument(s): {diff}")
        return {**DEFAULT_SETTINGS, **parser_kwargs}

    @staticmethod
    def _parse(data: bytes, parser_kwargs: Dict[str, Any]) -> pd.DataFrame:
        """
        Parse the given data string into a `DataFrame`

        Parameters
        ----------
        data:
            string representation of the data to parse
        parser_kwargs:
            parser parameters, will be 'translated', if necessary, and are
            passed to `pandas.read_csv`

        Returns
        -------
        parsed data
        """

        kwargs = {**parser_kwargs}
        timestamp_column = kwargs.pop("timestamp_column")
        timestamp_format = kwargs.pop("timestamp_format")
        header = kwargs.pop("header") - 1

        try:
            df = pd.read_csv(BytesIO(data), header=header, **kwargs)
            df.iloc[:, timestamp_column] = pd.to_datetime(
                df.iloc[:, timestamp_column], format=timestamp_format
            )
        except (pd.errors.EmptyDataError, IndexError):
            df = pd.DataFrame()

        return df

    @staticmethod
    def _to_observations(
        row: pd.Series, timestamp_column: int, origin: str
    ) -> List[Observation]:
        """
        Convert a given `Series` into a list of `Observations`

        Parameters
        ----------
        row:
            data to convert
        origin:
            value to store in `Observation.origin`

        Returns
        -------
        `Observations` iterator
        """
        observations = []
        if row.empty:
            return observations
        timestamp = row.iloc[timestamp_column]

        for i, value in enumerate(row):
            if i == timestamp_column:
                continue
            observations.append(
                Observation(timestamp=timestamp, value=value, position=i, origin=origin)
            )
        return observations

    def do_parse(self):
        parser_kwargs = self._prep_parser_kwargs(
            self.datastore.get_parser_parameters(self.name)
        )
        content = self.rawdata_source.read()
        data = self._parse(content, parser_kwargs)

        self.set_progress_length(np.prod(data.shape))

        for _, row in data.iterrows():
            try:
                observations = self._to_observations(
                    row, parser_kwargs["timestamp_column"], self.rawdata_source.src
                )
                self.datastore.store_observations(observations)
            except NanNotAllowedHereError:
                pass
            self.update_progress(len(row))
