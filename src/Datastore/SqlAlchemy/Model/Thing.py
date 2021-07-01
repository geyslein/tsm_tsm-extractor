# coding: utf-8
from sqlalchemy import BigInteger, Column, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Thing(Base):
    __tablename__ = 'thing'

    id = Column(BigInteger, primary_key=True, server_default=text(
        "nextval('thing_id_seq'::regclass)"
    ))
    name = Column(String(200), nullable=False)
    uuid = Column(UUID, nullable=False, unique=True)
    description = Column(Text)
    properties = Column(JSONB(astext_type=Text()))
