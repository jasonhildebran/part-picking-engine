from sqlalchemy import Column, Integer, String, Enum as SQLAlchemyEnum, JSON
from database import Base
import enum

class SourceType(str, enum.Enum):
    API_CACHE = "API_CACHE"
    DEEP_SCRAPE = "DEEP_SCRAPE"
    USER_UPLOAD = "USER_UPLOAD"

class ComponentVault(Base):
    __tablename__ = "component_vault"

    id = Column(Integer, primary_key=True, index=True)
    part_number = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    source_type = Column(SQLAlchemyEnum(SourceType), nullable=False)
    specs = Column(JSON, nullable=True)
