#! /usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import itertools
from io import BytesIO
from typing import Any, Dict, Sequence, Tuple, Type

import numpy as np
import pandas as pd

from MockDatasource import MockDataSource
from MockDatastore import MockDatastore
from Datastore.Observation import Observation
from Parser.CsvParser import REQUIRED_SETTINGS, CsvParser


RANDOM_SEED = 999


class TestCSVParser(unittest.TestCase):

    TYPES = [float, int]
    SHAPES = [(10, 10), (0, 0), (1, 0), (0, 1), (1, 1), (1, 25), (25, 1), (25, 25)]
    PARAMETERS = [
        {
            "timestamp_column": 0,
            "timestamp_format": "%Y-%m-%dT%H:%M:%S",
            "delimiter": ","
        },
        {
            "timestamp_column": 1,
            "timestamp_format": "%d/%m/%Y %H:%M:%S",
            "delimiter": ";"
        },
    ]

    @staticmethod
    def _generate_data(
        dtype: Type, shape: Tuple[int, int], timestamp_column: int
    ) -> pd.DataFrame:
        """
        generate test data with type `dtype` and shape `shape`
        """
        np.random.seed(RANDOM_SEED)
        out = pd.DataFrame(
            data=(np.random.random(np.prod(shape)).reshape(shape) * 1000).astype(dtype),
        )
        if not out.empty:
            out.insert(
                loc=timestamp_column,
                column="index",
                value=pd.date_range(start="2020-01-01", freq="1Min", periods=shape[0]),
            )
        return out.round(12)

    @staticmethod
    def _to_bytes(df: pd.DataFrame, parameters: Dict[str, Any]) -> bytes:
        """
        convert `df` into it's bytes representation
        """
        data = df.copy()
        if not data.empty:
            timestamp_column = parameters["timestamp_column"]
            timestamp_format = parameters["timestamp_format"]
            data.iloc[:, timestamp_column] = data.iloc[:, timestamp_column].dt.strftime(
                timestamp_format
            )
        fobj = BytesIO()
        data.to_csv(
            fobj,
            sep=parameters["delimiter"],
            header=True,
            index=False,
        )
        fobj.seek(0)
        return fobj.read()

    @staticmethod
    def _to_frame(observations: Sequence[Observation], timestamp_column=0) -> pd.DataFrame:
        """
        convert a Sequence of `Observation`s into a `DataFrame`
        """
        if observations:
            df = pd.DataFrame(
                [(o.timestamp, o.position, o.value) for o in observations],
            )
            out = df.pivot_table(index=0, columns=1, values=2)
            out.insert(loc=timestamp_column, column="index", value=out.index)
            out = out.reset_index(drop=True)
            return out
        return pd.DataFrame()

    def _assert_df_equality(self, left: pd.DataFrame, right: pd.DataFrame) -> None:
        """
        check whether two datafreames are identical (enough)
        """
        if not (left.empty and right.empty):
            self.assertTrue(np.array_equal(left, right), 'Input and output data is not the same.')
            self.assertTrue((left.index == right.index).all())

    def test_failure_on_missing_parameters(self):
        """
        test, if missing but required parser settings raise an exception
        """
        for key in REQUIRED_SETTINGS:
            with self.assertRaises(TypeError):
                CsvParser._prep_parser_kwargs(
                    {k: None for k in REQUIRED_SETTINGS if k != key}
                )

    def test_parsing(self):
        """
        test the basic parsing functionality
        """
        for dtype, shape, parameters in itertools.product(
            self.TYPES, self.SHAPES, self.PARAMETERS
        ):
            expected = self._generate_data(dtype, shape, parameters["timestamp_column"])
            content = self._to_bytes(expected, parameters)
            kwargs = {"header": 1, "delimiter": ",", **parameters}
            got = CsvParser._parse(content, kwargs)
            self._assert_df_equality(expected, got)

    def test_observations(self):
        """
        test the converions from a `DataFrame` into a sequence of `Observation`s
        """
        for dtype, shape in itertools.product(self.TYPES, self.SHAPES):
            expected = self._generate_data(dtype, shape, timestamp_column=0)
            observations = sum(
                CsvParser._to_observations(
                    expected, timestamp_column=0, origin="/unit/test"
                ),
                [],
            )
            got = self._to_frame(observations, timestamp_column=0)
            self._assert_df_equality(expected, got)

    def test_integration(self):
        """
        test the system integration
        """
        kwargs = {
            "header": 1,
            "timestamp_column": 0,
            "delimiter": ",",
            "timestamp_format": "%Y-%m-%dT%H:%M:%S",
        }
        expected = self._generate_data(
            float, (12, 10), timestamp_column=kwargs["timestamp_column"]
        )

        datastore = MockDatastore(None, None, kwargs)
        datasource = MockDataSource(self._to_bytes(expected, kwargs))
        parser = CsvParser(datasource, datastore)

        parser.do_parse()

        got = self._to_frame(datastore.get_observations(), kwargs["timestamp_column"])
        self._assert_df_equality(expected, got)


if __name__ == "__main__":
    unittest.main()
