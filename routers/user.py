import logging
import uuid
from typing import Optional

from auth.google_open_id import GoogleOpenIdClient
from fastapi import APIRouter, Request, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import RedirectResponse, JSONResponse
from lib.exception import UserAuthorizationException
import google_auth_oauthlib.flow

from models.user import User
from lib.token_util import (
    AuthTokenBearer,
    AuthToken,
    AccessToken,
    AccessTokenBearer,
    set_cookie_token,
    delete_cookie_token,
)
from lib.config import GOOGLE_CLIENT_SECRETS_FILE, GOOGLE_SCOPES, DOMAIN
from . import cache


auth_token_scheme = AuthTokenBearer()
access_token_scheme = AccessTokenBearer()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)
router = APIRouter()

tmp_uuid = None


@router.get("/login-redirect")
async def login_redirect():
    """
    [1] Redirect user to Google login page.
    - write ephermal authorize state into 'cache'
    - pass callback url and wait for callback.
    """ 
    auth_uuid = uuid.uuid4().hex
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE,
        scopes=GOOGLE_SCOPES,
    )
    flow.redirect_uri=f"{DOMAIN}/user/oauth2-callback"
    logger.debug(f"flow.redirect_uri={flow.redirect_uri}")

    auth_url: str
    state: str
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
    )
    await cache.set(state, auth_uuid)
    logger.debug(f"Redirect to url: {auth_url} with auth uuid: {auth_uuid} and state: {state}")
    return RedirectResponse(auth_url)


@router.get("/oauth2-callback")
async def oauth2callback(state: str, code: str, scope: str, req: Request):
    """
    [2] Callback invoked by the Google Authorization Service when the user logs in to Google's pop-up.

    Receives an authentication_token from Google which then
    exchanges for an access_token. The latter is used to
    gain user information from Google's userinfo_endpoint.

    Args:
        state: an unique uuid for auth status in cache.
        code: authorization code from google for authorization token.
        scope: authorization scope: openID + email.
        request: The incoming request as redirected by Google
    """
    auth_uuid = await cache.get(state.strip())

    if not auth_uuid:
        logger.error(f"Can't find auth status: {state} from cache: {cache._cache}")
        raise UserAuthorizationException()

    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE,
        scopes=GOOGLE_SCOPES,
        state=state,
    )
    flow.redirect_uri=f"{DOMAIN}/user/oauth2-callback"
    try:
        logger.debug(f"fetch token req.url={req.url} and flow.redirect_uri={flow.redirect_uri}")
        flow.fetch_token(code=code)
    except Exception as e:
        logger.error(f"Fetch token failed with error: \n{e}")
        raise UserAuthorizationException()

    email = await GoogleOpenIdClient(flow.credentials).get_user_email()
    logger.debug(f"Got user email: {email} from Google.")

    user: Optional[User] = User.get_by_name(email)
    if not user:
        logger.info(f"new user with email: {email}. Creating record.")
        user = User.new(email)

    await cache.delete(state.strip())
    rsp = RedirectResponse(url=f"{DOMAIN}/user/login")
    await set_cookie_token(rsp, AuthToken(user.id))

    return rsp


@router.get("/login")
async def login(
    user: User = Depends(auth_token_scheme)
):
    """
    [3] Re-create user from auth_token, generate access token and then set cookie's user status
    and return. 
    """
    logger.debug(f"Login invoked with user.name={user.name}")
    rsp = JSONResponse(
        content=jsonable_encoder({
            "username": user.name,
            "log-in": True,     
        }),
    )

    access_token = AccessToken(user.id)
    await set_cookie_token(rsp, access_token)
    
    return rsp


@router.get("/logout")
async def logout(user: User = Depends(access_token_scheme)):
    rsp = JSONResponse(
        content=jsonable_encoder({
            "username": user.name,
            "log-in": False,     
        }),
    )
    delete_cookie_token(rsp)

    return rsp


@router.get("/status")
async def status(user: User = Depends(access_token_scheme)):
    return f"login-user: {user}"