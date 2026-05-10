"""SQLAlchemy declarative base. Every ORM model inherits from Base."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
