from sqlalchemy import Boolean, Column, Integer, String, DateTime

from redirect.db import Base


class Link(Base):
    """Model of a short link that defines slug and target of a redirect."""
    __tablename__ = "short_link"

    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime)
    modified = Column(DateTime)
    source = Column(String)
    slug = Column(String, index=True)
    enabled = Column(Boolean)
    viewed = Column(Integer)
    creator_id = Column(Integer, index=True)
