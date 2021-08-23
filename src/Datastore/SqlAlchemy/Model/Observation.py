# coding: utf-8
import enum

import sqlalchemy_jsonfield
from sqlalchemy.dialects import oracle
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, String, text, \
    UniqueConstraint, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from Datastore.SqlAlchemy.Model import Datastream
from Datastore.SqlAlchemy.Model.IntEnum import IntEnum

Base = declarative_base()
metadata = Base.metadata


class ResultType(enum.IntEnum):
    # [(1, 'Number'), (2, 'String'), (3, 'JSON'), (4, 'Bool')]
    Number = 1
    String = 2
    Json = 3
    Bool = 4


class Observation(Base):
    __tablename__ = 'observation'
    __table_args__ = (
        UniqueConstraint('datastream_id', 'result_time'),
    )

    id = Column(BigInteger, primary_key=True, server_default=text(
        "nextval('observation_id_seq'::regclass)"
    ))
    phenomenon_time_start = Column(DateTime(True))
    phenomenon_time_end = Column(DateTime(True))
    result_time = Column(oracle.TIMESTAMP, nullable=False)  # enable oracle to store milliseconds
    result_type = Column(IntEnum(ResultType), nullable=False, default=ResultType.Number)
    result_number = Column(Float(53))
    result_string = Column(String(200))
    result_json = Column(sqlalchemy_jsonfield.JSONField())
    result_boolean = Column(Boolean)
    result_latitude = Column(Float(53))
    result_longitude = Column(Float(53))
    result_altitude = Column(Float(53))
    result_quality = Column(sqlalchemy_jsonfield.JSONField())
    valid_time_start = Column(DateTime(True))
    valid_time_end = Column(DateTime(True))
    parameters = Column(sqlalchemy_jsonfield.JSONField())
    datastream_id = Column(
        ForeignKey(Datastream.id, deferrable=True, initially='DEFERRED'),
        nullable=False, index=True
    )

    datastream = relationship(Datastream)
