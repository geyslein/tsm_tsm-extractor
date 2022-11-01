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
import saqc
from saqc.core.core import DictOfSeries


def parse_qaqc_config(datastore):
    thing = datastore.sqla_thing
    idx = thing.properties["QAQC"]["default"]
    config = thing.properties["QAQC"]["configs"][idx]

    if config["type"] != "SaQC":
        raise NotImplementedError("only configs of type SaQC are supported currently")
    else:
        logging.debug(f"raw-config: {config}")

    config_df = pd.DataFrame(config["tests"])
    config_df["window"] = parse_window(config["context_window"])

    # example `config_df`
    #                                     kwargs   function  position          window
    # 0                   {'max': 100, 'min': 0}  flagRange         0 0 days 01:00:00
    # 1                    {'max': 98, 'min': 2}  flagRange         2 0 days 01:00:00
    # 2  {'window': '60Min', 'min_residuals': 5}    flagMAD         0 0 days 01:00:00
    return config_df


def parse_window(window) -> pd.Timedelta | int:
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
    main_data = pd.read_sql(
        query.statement,
        query.session.bind,
        parse_dates=True,
        index_col="result_time",
    )

    if main_data.empty:
        return None

    # numeric window
    # --------------
    # get window-many additional observations
    # preceding the first observation of the new data.
    # the window define a number of observations e.g. `500`
    if isinstance(window, int):

        query = base_query.filter(
            Observation.result_time < less_recent,
        ).order_by(sqlalchemy.desc(Observation.result_time))

        chunks = pd.read_sql(
            query.statement,
            query.session.bind,
            parse_dates=True,
            index_col="result_time",
            chunksize=window,
        )
        try:
            window_data = next(chunks)
        except StopIteration:  # no data
            window_data = pd.DataFrame([])

    # datetime window
    # ---------------
    # get arbitrary many observations, which lies in the
    # window before the first observation. The window is
    # defined by a datetime-offset e.g. `'7d'`
    else:
        window: pd.Timedelta
        query = base_query.filter(
            Observation.result_time < less_recent,
            Observation.result_time >= less_recent - window,
        )
        window_data = pd.read_sql(
            query.statement,
            query.session.bind,
            parse_dates=True,
            index_col="result_time",
        )

    if window_data.empty:
        data = main_data
    else:
        data = pd.concat([main_data, window_data], sort=True)

    return data


def get_data(datastore: SqlAlchemyDatastore, config: pd.DataFrame):
    if config.empty:
        return

    unique_pos = config["position"].unique()
    data = DictOfSeries(columns=list(map(str, unique_pos)))

    # hint: window is the same for whole config
    window = config.loc[0, "window"]

    dummy = pd.Series([], dtype=float, index=pd.DatetimeIndex([]))

    for pos in unique_pos:
        var_name = str(pos)

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
    for idx, row in config.iterrows():
        # var is position for now, until SMS is inplace
        var = str(row["position"])
        func = row["function"]
        kwargs = row["kwargs"]
        info = config.loc[idx].to_dict()
        data = run_saqc_funtion(data, var, func, kwargs, info)

    return data


def run_saqc_funtion(qc_obj, var_name, func_name, kwargs, info):
    method = getattr(qc_obj, func_name, None)
    logging.debug(f"running SaQC with {info=}")
    qc_obj = method(var_name, **kwargs)
    return qc_obj
