# coding: utf-8
import sqlalchemy_jsonfield
from sqlalchemy import BigInteger, Column, String, Text, text, JSON
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
    properties = Column(sqlalchemy_jsonfield.JSONField())

    def get_parser_parameters(self, parser_type: str) -> dict:
        try:
            for parser in self.properties.get('parsers'):
                if parser.get('type') == parser_type:
                    return parser.get('settings')
        except TypeError:
            pass  # when there is no "parsers" array in the properties json object

        raise Exception(
            'Thing "{}" (UUID: {}) does not provide settings for parser type "{}"'.format(
                self.name,
                self.uuid,
                parser_type
            )
        )
