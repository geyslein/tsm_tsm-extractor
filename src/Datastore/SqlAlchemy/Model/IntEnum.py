from sqlalchemy import TypeDecorator, Integer, Enum


class IntEnum(TypeDecorator):
    """
    Enumeration type to allow Django model like choices with integer representation in database

    @see https://medium.com/the-andela-way/how-to-create-django-like-choices-field-in-flask-sqlalchemy-1ca0e3a3af9d
    """
    @property
    def python_type(self):
        pass

    def process_literal_param(self, value, dialect):
        pass

    impl = Integer()
    cache_ok = True

    def __init__(self, enumtype, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        if isinstance(value, Enum):
            return value
        elif isinstance(value, int):
            return value
        return value.value

    def process_result_value(self, value, dialect):
        return self._enumtype(value)