import logging

from fastapi import APIRouter, Depends, HTTPException
from lib.exception import HTTP_INTERNAL_SERVER_ERROR, HTTP_BAD_REQUEST
from lib.token_util import AccessTokenBearer
from models.user import User
from models.workflow import Workflow, WorkflowType, Args
from pydantic import BaseModel
from typing import List, Set, Optional


logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


router = APIRouter()
access_token_scheme = AccessTokenBearer()


class WorkflowMetadata(BaseModel):
    id: int
    video_uuid: Optional[str]
    video_title: Optional[str]
    create_at: int
    transcript_fmts: Set[str]
    auto_upload: bool
    status: int


@router.post("/add", status_code=201)
async def add(
    args: str,  # json args
    type: int,  # WorkflowType
    user: User = Depends(access_token_scheme),
):
    try:
        arg_obj = Args.from_json(args)
    except Exception as e:
        logger.exception(
            f"Failed to parse args: {args} as json due to exp: {e}"
        )
        raise HTTPException(
            status_code=HTTP_BAD_REQUEST,
            detail=str(e)
        ) from e

    try:
        workflow = Workflow.new(user, arg_obj, type)
    except Exception as e:
        logger.exception(f"create new workfow failed with the exp: {e}")
        raise HTTPException(
            status_code=HTTP_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e
    logger.info(f"workflow: {workflow.id} created.")

    return {"workflow_id": workflow.id}


@router.post("/list")
async def list_workflows(
    type: int,
    user: User = Depends(access_token_scheme),
) -> List[WorkflowMetadata]:
    metadatas = []
    try:
        workflows = Workflow.list(user.id, WorkflowType(type))
    except Exception as e:
        logger.exception(f"Get workfows failed with the exp: {e} "
                         f"for type: {type} and user: {user}")
        raise HTTPException(
            status_code=HTTP_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e

    metadatas = [
        WorkflowMetadata(
            id=w.id,
            video_uuid=w.args.video_uuid,
            video_title=None,  # TODO dump this from the video table.
            create_at=w.create_at,
            transcript_fmts=w.args.transcript_fmts,
            auto_upload=w.args.auto_upload,
            status=w.status.value
        ) for w in workflows
    ]

    if len(metadatas) == 0:
        logger.warning(f"Found no workflow for type: {type} and user: {user}")
    return metadatas
