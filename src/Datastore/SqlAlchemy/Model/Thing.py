# coding: utf-8
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, SmallInteger, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Thing(Base):
    __tablename__ = 'thing'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('thing_id_seq'::regclass)"))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    properties = Column(JSONB(astext_type=Text()))