from typing import Any, Annotated
from typing import Optional
import logging

from fastapi import APIRouter, Request, Depends, Body
import aiohttp

from lib.config import OPENAI_API_KEY
from lib.exception import DependencyException, HTTP_BAD_GATEWAY
from lib.token_util import AccessTokenBearer
from models.user import User


OPENAI_DOMAIN = "https://api.openai.com/v1/"


logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


router = APIRouter()
access_token_scheme = AccessTokenBearer()


# TODO /docs able to pass Parameters to this.
# TODO having "mock" as paramter for all api???
@router.post("/v1/audio/transcriptions")
async def transcriptions(
    # file: Annotated[str, Body(example="audio.mp3")], # TODO regex here??
    # model: Annotated[str, Body(example="whisper-1")],
    # prompt: Annotated[Optional[str], Body()],
    # response_format: Annotated[Optional[str], Body(example="json")], # default json
    # temperature: Annotated[Optional[float], Body(ge=0, le=1)],
    # language: Annotated[Optional[str], Body(description="input language in ISO-639-1")],
    req: Request,
    user: User = Depends(access_token_scheme),
):          
    """
    - file: The audio file to transcribe, in one of these formats: mp3, mp4, mpeg, mpga, m4a, wav, or webm.
    
    - model: ID of the model to use. Only whisper-1 is currently available.
    
    - prompt: An optional text to guide the model's style or continue a previous audio segment.
    The prompt should match the audio language.
    
    - response_format: The format of the transcript output, in one of these options: json, text, 
    srt, verbose_json, or vtt.

    - temperature: The sampling temperature, between 0 and 1. Higher values like 0.8 will make the 
    output more random, while lower values like 0.2 will make it more focused and deterministic. If 
    set to 0, the model will use log probability to automatically increase the temperature until certain 
    thresholds are hit.
    
    - language: The language of the input audio. Supplying the input language in ISO-639-1 format will 
    improve accuracy and latency.
    """
    return await forward(
        api_url=f"{OPENAI_DOMAIN}/audio/transcriptions",
        req=req,
        user=user,
    )

async def forward(
    api_url: str,
    req: Request,
    user: User = Depends(access_token_scheme),
): 
    logger.debug(f"user: {user.name} is requesting for: {api_url}")
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    req_json = await req.json()
    rsp_json = None
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                api_url,
                json=req_json,
            ) as rsp:
                rsp_json = await rsp.json()
                logger.debug(f"Got response:\n {str(rsp_json)[:600]}")
    except Exception as e:
        raise DependencyException(
            status_code=HTTP_BAD_GATEWAY,
            detail=f"Request to: '{api_url}' failed with error: {e}",
        )
    return rsp_json