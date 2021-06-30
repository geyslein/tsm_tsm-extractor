# coding: utf-8
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, SmallInteger, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from Datastore.SqlAlchemy.Model import Thing

Base = declarative_base()
metadata = Base.metadata


class Datastream(Base):
    __tablename__ = 'datastream'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('datastream_id_seq'::regclass)"))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    properties = Column(JSONB(astext_type=Text()), nullable=False)
    thing_id = Column(ForeignKey(Thing.id, deferrable=True, initially='DEFERRED'), nullable=False,
                      index=True)

    thing = relationship(Thing)
