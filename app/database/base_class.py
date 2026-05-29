from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    Core SQLAlchemy 2.0 Base class to prevent import circularity.
    """
    pass
