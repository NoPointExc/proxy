import json
import logging
import time

from enum import Enum
from lib.sqlite_connection_manager import SQLiteConnectionManager
from models.user import User
from pydantic import BaseModel, ValidationError
from typing import Optional, List, Any, Tuple, Set, Mapping


SELECT_MAX = 1000

logger = logging.getLogger("uvicorn.error")


def now() -> int:
    return int(time.time())


class WorkflowType(Enum):
    VIDEO = 1


class Status(Enum):
    TODO = 1
    LOCKED = 2
    CLAIMED = 3
    WORKING = 4
    ERROR = 5
    FAILED = 6
    DONE = 7


class Args(BaseModel):
    """
    One Example:
    {
        "video_uuid": "vO_yw27CCi4",
        "auto_upload": "false",
        "language": "CN",
        "transcript_fmts": ["srt"],
        "promotes": "元青花"
    }
    """
    video_uuid: Optional[str]
    auto_upload: bool
    language: Optional[str]
    transcript_fmts: Set[str]
    promotes: Optional[str]

    def to_json(self) -> Mapping[str, Any]:
        return self.json()

    @classmethod
    def from_json(cls, json_str: str) -> "Args":
        arg = cls(
            video_uuid=None,
            auto_upload=False,
            language=None,
            transcript_fmts=set(),
            promotes=None
        )
        try:
            arg = cls.model_validate_json(json_str)
        except ValidationError as e:
            logger.exception(
                f"Failed to parse: {json_str} as Args objection "
                f"due to exp: {e}, fallback to default values"
            )
            parsed = {}
            try:
                parsed = json.dumps(json_str)
            except Exception as e:
                logger.exception(
                    f"Failed to parse {json_str} as "
                    f"a json due to exp: {e}"
                )
                arg.video_uuid = parsed.get("video_uuid", None)
                arg.auto_upload = parsed.get("auto_upload", False)
                arg.language = parsed.get("language", None)
                arg.transcript_fmts = parsed.get("transcript_fmts", {})
                arg.promotes = parsed.get("promotes", None)

        return arg


class Workflow(BaseModel):
    """
    A workflow instance in the sql table 'workflow'.
    Sql table like:
    CREATE TABLE workflow (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        create_at INTEGER,
        args TEXT,
        -- 1: video_workflow
        type INTEGER,
        -- 0: todo --1 locked --2 claimed ...
        status INTEGER
    )

    'args' is a json string repsentation of `Args`. see `class Args`
    """
    id: int
    user_id: int
    create_at: int
    args: Args
    type: WorkflowType = WorkflowType.VIDEO
    status: Status = Status.TODO

    def __str__(self) -> str:
        return self.json()

    def __repr__(self) -> str:
        return self.__str__()

    def to_values(self) -> Tuple[Any]:
        return (
            self.user_id,
            self.create_at,
            self.args.to_json(),
            self.type.value,
            self.status.value,
        )

    @classmethod
    def from_values(cls, values: Tuple[Any]) -> "Workflow":
        return Workflow(
            id=values[0],
            user_id=values[1],
            create_at=values[2],
            args=Args.from_json(values[3]),
            type=WorkflowType(values[4]),
            status=Status(values[5]),
        )

    @classmethod
    def new(cls, user: User, args: Args, type: WorkflowType) -> "Workflow":
        sqlite = SQLiteConnectionManager()

        workflow = Workflow(
            id=-1,
            user_id=user.id,
            create_at=now(),
            args=args,
            type=type,
            status=Status.TODO,
        )
        sql = """
            INSERT INTO
                workflow (user_id, create_at, args, type, status)
            VALUES
                (?, ?, ?, ?, ?)
        """

        try:
            with sqlite.connect() as connection:
                cursor = connection.cursor()
                cursor.execute(
                    sql,
                    workflow.to_values()
                )
                workflow.id = cursor.lastrowid
                connection.commit()
                logger.debug(
                    f"inserted new workflow with id: {workflow.id} "
                )
        except Exception as e:
            raise Exception(
                f"Failed to insert workflow with sql:\n{sql}, "
                f"values={workflow.to_values()} due to error:\n {e}"
            ) from e

        return workflow


class WorkflowMetadata(BaseModel):
    id: int
    create_at: int
    status: int
    uuid: Optional[str]
    snippt: Mapping[str, str]
    transcript: Mapping[str, str]

    @classmethod
    def from_values(cls, values: Tuple[Any]) -> "WorkflowMetadata":
        return WorkflowMetadata(
            id=values[0],
            create_at=values[1],
            status=values[2],
            uuid=values[3],
            snippt=json.loads(values[4]),
            transcript=json.loads(values[5]),
        )

    @classmethod
    def list(
        cls,
        user_id: int,
        type: WorkflowType,
    ) -> List["WorkflowMetadata"]:
        sql = """
            SELECT
                w.id, w.create_at, w.status,
                v.uuid, v.snippt, v.transcript
            FROM workflow as w JOIN video as v
                ON w.id = v.workflow_id AND w.user_id = v.user_id
            WHERE
                w.user_id = ? AND type = ?
        """
        sqlite = SQLiteConnectionManager()
        values = (user_id, type.value)

        try:
            with sqlite.connect() as connection:
                cursor = connection.cursor()
                cursor.execute(sql, values)
                rows = cursor.fetchmany(SELECT_MAX)
        except Exception as e:
            raise Exception(
                f"Failed to list workflow with sql:\n{sql} "
                f"due to exp: {e}"
            ) from e

        metadatas = [WorkflowMetadata.from_values(r) for r in rows]
        if len(metadatas) == 0:
            logger.warning(
                "Found new workflow for "
                f"user_id: {user_id}, type: {type}"
            )
        return metadatas
