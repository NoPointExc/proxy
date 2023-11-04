import logging
import time

from enum import Enum
from lib.exception import ResourceNotFoundException
from lib.sqlite_connection_manager import SQLiteConnectionManager
from typing import Optional


logger = logging.getLogger("uvicorn.error")


class Format(Enum):
    JSON = "json"
    TEXT = "text"
    SRT = "srt"


class Resource:
    """
    class Resource:
    - type: Enum (json, text, srt, verbose_joson, vtt) etc
    - cost: int . # of token cost 
    - paid: bool # true when paid.
    - createTime: int
    - PayTime: int
    - raw: byte/blob
    """

    def __init__(
        self,
        id: int,
        type: Format,
        cost: int,
        paid: bool,
        raw: bytes,
        create_at: int,
        pay_at: int,
    ) -> None:
        self.id = id
        self.type = type
        self.cost = cost
        self.paid = paid
        self.create_at = create_at
        self.pay_at = pay_at
        self.raw = raw

    def __repr__(self) -> str:
        return (
            f"Resource(id={self.id}, type={self.type}, raw={self.raw})"
        )

    def __str__(self) -> str:
        return self.__repr__()

    @classmethod
    def new(cls, type: str, cost: int, paid: bool, raw: bytes) -> "Resource":
        create_at: int = int(time.time())
        sqlite = SQLiteConnectionManager()
        id: Optional[int] = None
        pay_at = -1
        try:
            with sqlite.connect() as connection:
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO resource "
                    "(type, cost, paid, raw, create_at, pay_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (type, cost, paid, raw, create_at, pay_at)
                )
                id = cursor.lastrowid
                logger.debug(f"New resource id: {id}")
                connection.commit()
        except Exception as e:
            raise ResourceNotFoundException(f"Failed to write resource into sqlite3 with error:\n {e}") from e
        if id is None:
            raise ResourceNotFoundException("Failed to create resource id due to sqlite return empty new id")

        return Resource(id, type, cost, paid, raw, create_at, pay_at)

    @classmethod
    def get_by_id(cls, id: int) -> "Resource":
        try:
            with SQLiteConnectionManager().connect() as connection:
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT "
                    "id, type, cost, paid, create_at, pay_at, raw "
                    "FROM users "
                    "WHERE id = ?",
                    (id,)
                )
                row = cursor.fetchone()
        except Exception as e:
            logger.error(f"Failed to get user with id: {id} from sqlite3 with due to error:\n {e}")

        if row:
            _id, _type, _cost, _paid, _create_at, _pay_at, _raw = row
            return Resource(
                _id, _type, _cost, _paid, _raw, _create_at, _pay_at
            )
        raise ResourceNotFoundException(f"Can not found resoure with id {id}")
