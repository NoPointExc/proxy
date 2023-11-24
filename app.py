import logging

from fastapi import Request, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from lib.config import DOMAIN
from lib.const import USER_NAME_COOKIE_KEY
from lib.exception import UserAuthorizationExpiredException
from lib.token_util import delete_cookie_token
from routers import user,  openai_v1, stripe, workflow


logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


app = FastAPI()


# TODO limit the CORS
origins = [
    "*",
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:59397",
    "http://127.0.0.1:8000",
    "127.0.0.1:59397",
    "104.180.136.59",

]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router, prefix="/user")
app.include_router(openai_v1.router, prefix="/openai")
app.include_router(stripe.router, prefix="/payment")
app.include_router(workflow.router, prefix="/workflow")
app.mount("/", StaticFiles(directory="static/build/", html=True), name="index")


@app.exception_handler(UserAuthorizationExpiredException)
async def unicorn_exception_handler(
    req: Request,
    exp: UserAuthorizationExpiredException,
):
    logger.debug(f"Deleted expired cookie due to: {exp}")
    rsp = RedirectResponse(url=DOMAIN)
    delete_cookie_token(rsp)
    rsp.delete_cookie(key=USER_NAME_COOKIE_KEY)
    return rsp
