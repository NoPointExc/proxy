from typing import Optional, Tuple
import logging
import time

from lib.exception import UserNotFoundException
from lib.sqlite_connection_manager import SQLiteConnectionManager


logger = logging.getLogger("uvicorn.error")


# TODO use from pydantic import BaseModel
# https://nilsdebruin.medium.com/fastapi-google-as-an-external-authentication-provider-3a527672cf33
# https://github.com/kolitiri/fastapi-oidc-react


class User:

    def __init__(self, id: int, name: str, create_at: int) -> None:
        self.id = id
        self.name = name
        self.create_at = create_at

    def __repr__(self) -> str:
        return f"User(id='{self.id}', name={self.name}, create_at='{self.create_at}')"
    
    def __str__(self) -> str:
        return self.__repr__()
    
    @classmethod
    def new(cls, name: str) -> "User":
        create_at: int = int(time.time())
        sqlite = SQLiteConnectionManager()
        
        user_id: Optional[int] = None
        try:
            with sqlite.connect() as connection:
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO users (name, create_at) VALUES (?, ?)",
                    (name, create_at,)
                )
                user_id = cursor.lastrowid
                logger.debug(f"New user id: {user_id}")
                connection.commit()
        except Exception as e:
            raise UserNotFoundException(f"Failed to write user into sqlite3 with error:\n {e}") from e
        if user_id is None:
            raise UserNotFoundException("Failed to create user id due to sqlite return empty new id")

        return User(user_id, name, create_at)

    @classmethod
    def get_by_id(cls, id: int) -> "User":
        id_: int
        name_: str
        create_at_: int
        row: Optional[Tuple[int, int, Optional[str], str]] = None

        try:
            with SQLiteConnectionManager().connect() as connection:
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT id, create_at, name FROM users WHERE id = ?",
                    (id,)
                )
                row = cursor.fetchone()
        except Exception as e:
            logger.error(f"Failed to get user with id: {id} from sqlite3 with due to error:\n {e}")
        
        if row:
            id_, create_at_, name_ = row
            return User(id_, name_, create_at_)

        logger.error(f"Failed to user with id: {id}")
        raise UserNotFoundException("We can't found this user from database.")

    @classmethod
    def get_by_name(cls, name: str) -> Optional["User"]:
        id_: int
        name_: str
        create_at_: int
        row: Optional[Tuple[int, int, Optional[str], str]] = None

        try:
            with SQLiteConnectionManager().connect() as connection:
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT id, create_at, name FROM users WHERE name = ?", # use ? or () here???
                    (name,)
                )
                row = cursor.fetchone()
                logger.debug(f"row={row}")
        except Exception as e:
            logger.error(f"Failed to get user with name(email) {name} from sqlite3 with due to error:\n {e}")
            return None

        if row:
            id_, create_at_, name_ = row
            return User(id_, name_, create_at_)

        logger.info(f"Can not found user with name(email): {name} from db")
        return None


# test DB E2E
# $python3 -m models.user
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # test create
    # chestnut: User = User.new()
    # 1|1680367202|
    chestnut = User.get_by_id(1)
    logging.info(f"Got user: {chestnut}")
    chestnut.save_auth_state(f"mock_auth_state{int(time.time())}")
    logging.info(f"Upadted user: {chestnut}")
    chestnut.save_name(f"mock:woof:name{int(time.time())}")
    logging.info(f"Upadted user: {chestnut}")
    chestnut = User.get_by_id(1)
    logging.info(f"After re-get user: {chestnut}")
    # test_query()