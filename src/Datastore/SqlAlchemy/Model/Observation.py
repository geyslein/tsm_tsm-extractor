# coding: utf-8
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, SmallInteger, \
    String, Text, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from Datastore.SqlAlchemy.Model import Datastream

Base = declarative_base()
metadata = Base.metadata


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
    result_time = Column(DateTime(True), nullable=False)
    result_type = Column(SmallInteger, nullable=False)
    result_number = Column(Float(53))
    result_string = Column(String(200))
    result_json = Column(JSONB(astext_type=Text()))
    result_boolean = Column(Boolean)
    result_latitude = Column(Float(53))
    result_longitude = Column(Float(53))
    result_altitude = Column(Float(53))
    result_quality = Column(JSONB(astext_type=Text()))
    valid_time_start = Column(DateTime(True))
    valid_time_end = Column(DateTime(True))
    parameters = Column(JSONB(astext_type=Text()))
    datastream_id = Column(
        ForeignKey(Datastream.id, deferrable=True, initially='DEFERRED'),
        nullable=False, index=True
    )

    datastream = relationship(Datastream)
