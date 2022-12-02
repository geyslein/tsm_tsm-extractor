#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import typing
import warnings

import numpy as np
from tsm_datastore_lib import SqlAlchemyDatastore
from tsm_datastore_lib.SqlAlchemy.Model import Observation, Thing, Datastream

import logging
import sqlalchemy

import pandas as pd
from pandas.api.types import is_integer
import saqc
from saqc.core.history import History
from saqc.core.core import DictOfSeries
from tsm_datastore_lib.SqlAlchemyDatastore import DatastreamNotFoundError


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
        The datastore to fetch the config from and for.

    Notes
    -----
    The resulting config dataframe will have these columns:
     - 'position' : The datastream position to fetch the data,
        to be quality controlled (regular data).
     - 'window' : The (context) window. A non-negative integer
        or time-offset string, defining the range of data to
        fetch additionaly before the first regular observation.
        The window will have the same value over all rows.
     - 'function' : The function to execute on the data.
     - 'kwargs' : The arguments to pass to the function.

    Returns
    -------
    config: pd.DataFrame
    """
    thing = datastore.sqla_thing
    idx = thing.properties["QAQC"]["default"]
    config = thing.properties["QAQC"]["configs"][idx]

    if config["type"] != "SaQC":
        raise NotImplementedError("only QA/QC configurations of type "
                                  "'SaQC' are currently supported")
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

    return pd.concat([main_data, window_data], copy=False).sort_index()


def get_unique_positions(config) -> pd.Index:
    return pd.Index(config["position"].unique())


def position_to_varname(pos: int) -> str:
    """
    Dummy function.
    In a future version this should translate positions
    to real variable names via SMS-API.
    """
    return str(pos)


def varname_to_position(name: str) -> int:
    """
    Dummy function.
    In a future version this should translate
    varnames to positions via SMS-API.
    """
    return int(name)


def _extract_by_result_type(df: pd.DataFrame) -> pd.Series:
    """ Selects the column, specified as integer in the column 'result_type'. """
    def select(arr: np.ndarray): return arr[1+arr[0]]
    columns = pd.Index(['result_type', 'result_number', 'result_string', 'result_json', 'result_boolean'])
    return df[columns].apply(select, axis=1, raw=True)


def get_data(datastore: SqlAlchemyDatastore, config: pd.DataFrame) -> saqc.SaQC:
    unique_pos = get_unique_positions(config)
    data = DictOfSeries(columns=unique_pos.map(position_to_varname))

    # hint: window is the same for whole config
    window = config.loc[0, "window"]

    dummy = pd.Series([], dtype=float, index=pd.DatetimeIndex([]))

    for pos, var_name in zip(unique_pos, data.columns):
        try:
            datastream = datastore.get_datastream(pos)
        except DatastreamNotFoundError:
            logging.warning(f"no datastream for position {pos}")
            data[var_name] = dummy
            continue
        else:
            # keep track of the source datastream for debugging etc.
            config.loc[config["position"] == pos, "datastream_name"] = datastream.name

        raw = get_datastream_data(datastore, datastream, window)
        if raw is None:
            logging.info(f"no data for {datastream.name=}")
            data[var_name] = dummy
            continue

        try:
            data[var_name] = _extract_by_result_type(raw)
        except IndexError:
            logging.exception(f"extraction of data failed for {datastream.name=}")
            continue



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


def _last_valid_test(history: History) -> pd.Series:
    """
    todo: add this to saqc.History().
    Note:
        - may has NaNs
        - dtype: float, but int'ish (w/ NaNs)
    """
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='.*dtype for empty Series', category=FutureWarning)
        return history.hist.astype(float).agg(pd.Series.last_valid_index, axis=1)


def _map_meta(history: History) -> pd.DataFrame:
    """
    todo: add this to saqc.History().
    Note:
        - has rows with all NaNs, if never flagged
        - columns: ['func', 'args', 'kwargs']
        - dtype: object
    """
    columns = pd.Index(['func', 'args', 'kwargs'])
    if history.columns.empty or history.index.empty:
        # todo: this should be the condition for History.empty
        return pd.DataFrame(index=history.index, columns=columns, dtype=object)

    def _map(pos, meta):
        return pd.Series(None if np.isnan(pos) else meta[int(pos)], dtype=object)

    df = _last_valid_test(history).apply(_map, meta=history.meta)
    return df.reindex(columns, axis=1)


def _get_quality_information(history: History) -> pd.DataFrame:
    """ todo: add this to saqc.Flags(). """
    labels = _map_meta(history)
    labels['flag'] = history.squeeze(raw=True)
    return labels


def upload_qc_labels(data: saqc.SaQC, config: pd.DataFrame, datastore: SqlAlchemyDatastore):
    # we don't want data-derivates to be uploaded.
    # So we can't use all columns from data.
    # see also: #GL25
    # https://git.ufz.de/rdm-software/timeseries-management/tsm-extractor/-/issues/25
    positions = get_unique_positions(config)
    for pos in positions:
        var = position_to_varname(pos)
        df = _get_quality_information(data._flags.history[var])
        _upload_qc_labels(datastore, pos, df)


def update_observation(datastore: SqlAlchemyDatastore, datastream, result_time: pd.Timestamp, to_update: dict) -> None:
    """ todo: add this to tsm_datastore_lib.SqlAlchemyDatastore """
    # prevent cross-scripting, by disallowing 'null' and other values
    if not isinstance(result_time, pd.Timestamp):
        raise TypeError(type(result_time).__name__)
    datastore.session.query(Observation).filter(
        Observation.datastream == datastream,
        Observation.result_time == result_time
    ).update(to_update)


def to_jsonb(obj: typing.Any) -> dict | list | str | int | float | True | False | None:
    """
    Make any python object jsonb compatible.

    Any object (or inner item or sub object) that cannot
    be represented by the supported types, will be converted
    to a string representation, by simply calling `str` on it.
    Natively supported types are dict, list, str, int, float,
    True, False and None.
    """
    # default=str: use str() to parse non json-serializable objects
    # parse_constant=str: use str() for -Infinity/Infinity/NaN
    return json.loads(json.dumps(obj, default=str), parse_constant=str)


def _upload_qc_labels(datastore, position: int, df: pd.DataFrame):
    store: SqlAlchemyDatastore = datastore
    stream = datastore.get_datastream(position)

    def update(row: pd.Series):
        idx: pd.Timestamp = row.name  # index in df
        if np.isnan(row['flag']):
            data = dict()
        else:
            data = dict(row)
        update_observation(store, stream, idx, {'result_quality': to_jsonb(data)})

    df.apply(update, axis=1)
    datastore.session.commit()
