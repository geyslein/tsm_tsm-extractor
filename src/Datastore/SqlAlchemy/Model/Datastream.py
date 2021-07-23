# coding: utf-8
import sqlalchemy_jsonfield
from sqlalchemy import BigInteger, Column, ForeignKey, String, Text, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from Datastore.SqlAlchemy.Model import Thing

Base = declarative_base()
metadata = Base.metadata


class Datastream(Base):
    __tablename__ = 'datastream'
    __table_args__ = (
        UniqueConstraint('thing_id', 'position'),
    )

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('datastream_id_seq'::regclass)"))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    properties = Column(sqlalchemy_jsonfield.JSONField())
    position = Column(String(200), nullable=False)
    thing_id = Column(ForeignKey(
        Thing.id, deferrable=True, initially='DEFERRED'), nullable=False, index=True
    )

    thing = relationship(Thing)
