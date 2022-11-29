#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import datetime
import warnings

from tsm_datastore_lib import SqlAlchemyDatastore
from tsm_datastore_lib.SqlAlchemy.Model import Observation, Thing, Datastream

import logging
import sqlalchemy
from functools import lru_cache
from collections import OrderedDict
from typing import Dict, Callable, List

import pandas as pd
from pandas.api.types import is_integer
import saqc
from saqc.core.history import History
from saqc.core.core import DictOfSeries


def parse_qaqc_config(datastore):
    """
    Fetch the QAQC config from datastore and parse it into a DataFrame.

    Examples
    --------
    >>> parse_qaqc_config(datastore)
                                        kwargs   function  position  window
    0                   {'max': 100, 'min': 0}  flagRange         0       3
    1                    {'max': 98, 'min': 2}  flagRange         2       3
    2  {'window': '60Min', 'min_residuals': 5}    flagMAD         0       3

    Parameters
    ----------
    datastore : SqlAlchemyDatastore
        The datastore to fetch the config from/for.

    Notes
    -----
    The window column always have the same value over all rows.

    Returns
    -------
    config: pd.DataFrame
    """
    thing = datastore.sqla_thing
    idx = thing.properties["QAQC"]["default"]
    config = thing.properties["QAQC"]["configs"][idx]

    if config["type"] != "SaQC":
        raise NotImplementedError("only configs of type SaQC are supported currently")
    else:
        logging.debug(f"raw-config: {config}")

    config_df = pd.DataFrame(config["tests"])
    config_df["window"] = parse_window(config["context_window"])

    return config_df


def parse_window(window) -> pd.Timedelta | int:
    """Parse the `context_window` value of the config."""
    if isinstance(window, int) or isinstance(window, str) and window.isnumeric():
        window = int(window)
        is_negative = window < 0
    else:
        window = pd.Timedelta(window)
        is_negative = window.days < 0
    if is_negative:
        raise ValueError("window can't be negative")
    return window


def get_datastream_data(
    datastore: SqlAlchemyDatastore,
    datastream: Datastream,
    window: int | pd.Timedelta,
) -> pd.DataFrame | None:
    """
    Get data that has no quality flags yet.

    Parameters
    ----------
    datastore : SqlAlchemyDatastore
        Datastore to use.

    datastream : Datastream
        Datastream to fetch the data from

    window : int or pandas.Timedelta
        The context window of data to fetch additionally.

        If an integer, it defines the number of preceding observations to
        fetch additionally, before the first unprocessed observation.

        If a Timedelta, it defines an offset-window to fetch additionally
        before the timestamp of the first unprocessed observation.

        The first unprocessed observation is the earliest observation
        which never was quality-controlled before.

    Returns
    -------
    data: pd.DataFrame or None
    """
    query = datastore.session.query(Observation.result_time).filter(
        Observation.datastream == datastream,
        Observation.result_quality == sqlalchemy.JSON.NULL,
    )
    more_recent = query.order_by(sqlalchemy.desc(Observation.result_time)).first()
    less_recent = query.order_by(sqlalchemy.asc(Observation.result_time)).first()

    # no new observations
    if more_recent is None:
        # todo: throw warning ?
        return None
    else:
        more_recent = more_recent[0]
        less_recent = less_recent[0]

    base_query = datastore.session.query(Observation).filter(
        Observation.datastream == datastream
    )

    # get all new (unprocessed) data
    query = base_query.filter(
        Observation.result_time <= more_recent,
        Observation.result_time >= less_recent,
    )
    main_data: pd.DataFrame = pd.read_sql(
        query.statement,
        query.session.bind,
        parse_dates=True,
        index_col="result_time",
    )

    if main_data.empty:
        return None

    # numeric window
    if is_integer(window):  # detect numpy.int64
        query = (
            base_query.filter(
                Observation.result_time < less_recent,
            )
            .order_by(sqlalchemy.desc(Observation.result_time))
            .limit(window)
        )

    # datetime window
    else:
        query = base_query.filter(
            Observation.result_time < less_recent,
            Observation.result_time >= less_recent - window,
        )

    window_data: pd.DataFrame = pd.read_sql(
        query.statement,
        query.session.bind,
        parse_dates=True,
        index_col="result_time",
    )

    return pd.concat([main_data, window_data], sort=True, copy=False)


def get_unique_positions(config) -> pd.Index:
    return pd.Index(config["position"].unique())


def position_to_varname(pos: int) -> str:
    """
    Dummy function.
    In a future version this should translate positions
    to real variable names via SMS-API.
    """
    return str(pos)


def get_data(datastore: SqlAlchemyDatastore, config: pd.DataFrame) -> saqc.SaQC:
    unique_pos = get_unique_positions(config)
    data = DictOfSeries(columns=unique_pos.map(position_to_varname))

    # hint: window is the same for whole config
    window = config.loc[0, "window"]

    dummy = pd.Series([], dtype=float, index=pd.DatetimeIndex([]))

    for pos in unique_pos:
        var_name = position_to_varname(pos)

        datastream = datastore.get_datastream(pos)
        if datastream is None:
            logging.warning(f"no datastream for {pos=}")
            data[var_name] = dummy
            continue

        # keep track of the source datastream for debugging etc.
        config.loc[config["position"] == pos, "datastream_name"] = datastream.name

        raw = get_datastream_data(datastore, datastream, window)
        if raw is None:
            logging.warning(f"no data for {datastream.name=}")
            data[var_name] = dummy
            continue

        # todo: evaluate 'result_type'
        data[var_name] = raw["result_number"]

    return saqc.SaQC(data)


def run_qaqc_config(data: saqc.SaQC, config: pd.DataFrame):
    """
    Run a qc-tests from config on given data.

    Parameters
    ----------
    data : saqc.SaQC
        Hold data and quality labels (aka. flags).

    config : pd.dataFrame
        Collection of tests to run on data.

    Returns
    -------
    processed : saqc.SaQC
        Hold data and quality labels (aka. flags).
    """
    for idx, row in config.iterrows():
        var = position_to_varname(row["position"])
        func = row["function"]
        kwargs = row["kwargs"]
        info = row.to_dict()
        data = _run_saqc_function(data, var, func, kwargs, info)

    return data


def _run_saqc_function(
        qc_obj: saqc.SaQC, var_name: str, func_name: str, kwargs: dict, info: dict
):
    method = getattr(qc_obj, func_name, None)
    logging.debug(f"running SaQC with {info=}")
    qc_obj = method(var_name, **kwargs)
    return qc_obj


def _last_test(history: History) -> pd.Series:
    """ add as method to History(). """
    h = history.hist.astype(float)
    return h.apply(pd.Series.last_valid_index, axis=1)


def _map_meta(history: History) -> pd.Series:
    """
    add as method to History().
    Note: this keep NaNs
    """
    meta = history.meta
    def _map(pos): return str(meta[int(pos)])
    return _last_test(history).map(_map, na_action='ignore')


def _to_json(history: History) -> pd.DataFrame:
    """ add as method to Flags(). """
    # {"flag": 255.0, "function": "flagRange", "kwargs": {"min": 0, "max": 100}}
    # flags = history.squeeze(raw=True)
    labels = _map_meta(history)
    flags = "flag: \'" + history.squeeze().astype(str) + "\'"
    labels = labels.str[0] + flags + ', ' + labels[1:]
    labels = labels.fillna('{}')
    return labels


def upload_qc_labels(data: saqc.SaQC, config: pd.DataFrame, datastore: SqlAlchemyDatastore):

    # we don't want data-derivates to be uploaded.
    # So we can't use all columns from data.
    # see also: #GL25
    # https://git.ufz.de/rdm-software/timeseries-management/tsm-extractor/-/issues/25
    columns = get_unique_positions(config).map(position_to_varname)
    for var in columns:
        labels = _to_json(data._flags.history[var])
        print()
        print(labels)


def _upload_qc_labels(datastore, labels: pd.Series):
    pass
