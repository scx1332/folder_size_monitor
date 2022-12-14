import json
from enum import Enum

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base


BaseClass = declarative_base()


class SerializationMode(Enum):
    FULL = 1
    MINIMAL = 2


class PathInfo(BaseClass):
    __tablename__ = "path_info"
    id = Column(Integer, primary_key=True)
    path = Column(String, nullable=False)


class PathInfoEntry(BaseClass):
    __tablename__ = "path_info_entry"
    id = Column(Integer, primary_key=True)
    path_info = Column(Integer, ForeignKey("path_info.id"), nullable=False)
    files_checked = Column(Integer, nullable=False)
    files_failed = Column(Integer, nullable=False)
    total_size = Column(Integer, nullable=False)

    def to_json(self, mode=SerializationMode.FULL):
        if mode == SerializationMode.FULL:
            return {c.name: getattr(self, c.name) for c in self.__table__.columns}
        elif mode == SerializationMode.MINIMAL:
            return {
                "total_size": self.total_size
            }
        else:
            raise Exception(f"Unknown mode {mode}")


class LocalJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        self._mode = kwargs.pop('mode') if 'mode' in kwargs else None
        super().__init__(*args, **kwargs)

    def default(self, obj):
        if isinstance(obj, PathInfoEntry):
            return obj.to_json(mode=self._mode)
        return super().default(obj)


if __name__ == "__main__":
    pi1 = PathInfoEntry(path_info=1, files_checked=2, files_failed=3, total_size=4)
    pi2 = PathInfoEntry(path_info=10, files_checked=11, files_failed=12, total_size=13)

    print(json.dumps([pi1, pi2], cls=LocalJSONEncoder, indent=4, mode=SerializationMode.MINIMAL))
    print(json.dumps([pi1, pi2], cls=LocalJSONEncoder, indent=4, mode=SerializationMode.FULL))

