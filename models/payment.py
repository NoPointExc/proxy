import time
import logging

from typing import Optional
from enum import Enum
from pydantic import BaseModel

from lib.sqlite_connection_manager import SQLiteConnectionManager
from lib.exception import PaymentException
from lib.config import EMAIL


logger = logging.getLogger("uvicorn.error")


class Status(Enum):
    PENDING = 1
    SUCCESS = 2
    CANCELED = 3
    FAILED = 4


class Payment(BaseModel):
    id: int
    user_id: int
    create_at: int
    quantity: int
    status: Status

    @classmethod
    def create(cls, user_id: int, quantity: int) -> "Payment":
        payment = Payment(
            id=-1,
            user_id=user_id,
            create_at=int(time.time()),
            quantity=quantity,
            status=Status.PENDING,
        )

        sqlite = SQLiteConnectionManager()
        try:
            with sqlite.connect() as connection:
                cursor = connection.cursor()
                cursor.execute(
                    """
                    INSERT INTO
                        payment (user_id, create_at, quantity, status)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        user_id, payment.create_at,
                        quantity, payment.status.value
                    )
                )
                payment.id = cursor.lastrowid
                connection.commit()
        except Exception as e:
            logger.error(
                f"Failed to create Payment record in DB with error: {e}")
            raise PaymentException(
                "Failed to create payment. Please try again. "
                f"If you have further questions, please reach out to {EMAIL}"
            ) from e
        return payment

    @classmethod
    def get(cls, id: int) -> Optional["Payment"]:
        sqlite = SQLiteConnectionManager()
        row = None
        try:
            with sqlite.connect() as connection:
                cursor = connection.cursor()
                cursor.execute(
                    """
                        SELECT
                            id, user_id, create_at, quantity, status
                        FROM
                            payment
                        WHERE
                            id = ?
                    """,
                    (id, )
                )
                row = cursor.fetchone()
        except Exception as e:
            logger.error(
                f"Failed got gets payment {id} "
                f"from database due to error: {e}"
            )
            raise PaymentException(
                "Failed to retrive payment status. Please try again. "
                f"If you have further questions, please reach out to {EMAIL}"
            ) from e
        if row:
            return Payment(
                id=row[0],
                user_id=row[1],
                create_at=row[2],
                quantity=row[3],
                status=Status(row[4]),
            )
        return None

    def set_status(self, status: Status):
        sqlite = SQLiteConnectionManager()
        try:
            with sqlite.connect() as connection:
                cursor = connection.cursor()
                cursor.execute(
                    """
                    UPDATE
                        payment
                    SET
                        status = ?
                    WHERE
                        id = ?
                    """,
                    (status.value, self.id)
                )
                connection.commit()
        except Exception as e:
            logger.error(
                f"Failed to mark payment id: {self.id} "
                f"in DB as status: {status} with error: {e}"
            )
            raise PaymentException(
                "Failed to comfirm payment status. Please try again. "
                f"If you have further questions, please reach out to {EMAIL}"
            ) from e
        self.status = status
