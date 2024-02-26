import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from lib.config import EMAIL
from lib.exception import HTTP_INTERNAL_SERVER_ERROR, HTTP_BAD_REQUEST
from lib.token_util import AccessTokenBearer
from models.user import User
from models.workflow import Workflow, WorkflowType, Args, WorkflowMetadata


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
async def list(
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


@router.post("/delete")
async def delete(
    workflow_ids: List[int],
    user: User = Depends(access_token_scheme),
) -> None:
    try:
        Workflow.delete(workflow_ids, user.id)
    except Exception as e:
        error_msg = (
            f"Failed to delete workflow: {workflow_ids} for"
            f" user: {user} due to error: {e}"
        )
        logger.exception(error_msg)
        raise HTTPException(
            status_code=HTTP_INTERNAL_SERVER_ERROR, detail=error_msg
        ) from e


@router.post("/retry")
async def retry(
        workflow_id: int,
        user: User = Depends(access_token_scheme),
) -> None:
    workflow = Workflow.get(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=HTTP_BAD_REQUEST,
            detail=(
                f"Can not find workflow with id {id}. "
                f"Please reach out to {EMAIL} for helps."
            )
        )
    retry_workflow = Workflow.new(
        user=user,
        args=workflow.args,
        type=workflow.type
    )
    return {"workflow_id": retry_workflow.id}
