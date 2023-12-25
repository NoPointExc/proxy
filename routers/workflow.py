import logging

from fastapi import APIRouter, Depends, HTTPException
from lib.exception import HTTP_INTERNAL_SERVER_ERROR, HTTP_BAD_REQUEST
from lib.token_util import AccessTokenBearer
from models.user import User
from models.workflow import Workflow, WorkflowType, Args, WorkflowMetadata
from typing import List


logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


router = APIRouter()
access_token_scheme = AccessTokenBearer()


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
        metadatas = WorkflowMetadata.list(user.id, WorkflowType(type))
    except Exception as e:
        logger.exception(f"Get workfows failed with the exp: {e} "
                         f"for type: {type} and user: {user}")
        raise HTTPException(
            status_code=HTTP_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e

    if len(metadatas) == 0:
        logger.warning(f"Found no workflow for type: {type} and user: {user}")
    return metadatas
