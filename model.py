from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, Session, relationship

BaseClass = declarative_base()


class PathInfo(BaseClass):
    __tablename__ = "path_info"
    id = Column(Integer, primary_key=True)
    path = Column(String, nullable=False)


class PathInfoEntry(BaseClass):
    __tablename__ = "path_info_entry"
    id = Column(Integer, primary_key=True)
    #path_info = Column(PathInfo, ForeignKey("path_info.id"), nullable=False)
    files_checked = Column(Integer, nullable=False)
    files_failed = Column(Integer, nullable=False)
    total_size = Column(Integer, nullable=False)

