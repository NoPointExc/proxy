from typing import Optional, TypeVar
import logging
import time

from aiocache import Cache
from fastapi import Request
from fastapi.security.utils import get_authorization_scheme_param
import jwt

from models.user import User
from lib.config import (
    JWT_ALGORITHM,
    JWT_SECRET,
    AUTH_TOKEN_EXPIRE_S,
    ACCESS_TOKEN_EXPIRE_S,
)
from lib.exception import UserAuthorizationException


COOKIE_TOKEN_KEY = "Authorization"

cache = Cache()
logger = logging.getLogger("uvicorn.error")
T = TypeVar("T")

def now() -> int:
    return int(time.time())



class Token():

    def __init__(self, user_id: int, expire_after: int) -> None:
        self.expire_after = expire_after
        self.user_id = user_id
    

    @classmethod
    async def decode(cls, encoded_token: str) -> int:
        raw_token = None
        try:
            raw_token = jwt.decode(encoded_token, JWT_SECRET, JWT_ALGORITHM)
        except jwt.InvalidSignatureError as e:
            logger.error(f"Faild to decode token: {encoded_token} due to InvalidSignatureError: {e}")
            raise UserAuthorizationException()
        except jwt.ExpiredSignatureError as e:
            logger.error(f"Faild to decode token: {encoded_token} due to ExpiredSignatureError: {e}")
            raise UserAuthorizationException()
        except Exception as e:
            logger.error(f"Faild to decode token: {encoded_token} due to Unknown Exception: {e}")
            raise UserAuthorizationException()

        if not raw_token or "user_id" not in raw_token.keys():
            logger.error(
                f"Faild to decode token: {encoded_token} due decoded result is "
                f"empty or None. decoded raw token: {raw_token}"
            )
            raise UserAuthorizationException()
        
        return raw_token["user_id"]


    async def encode(self)-> str:
        # https://pyjwt.readthedocs.io/en/stable/usage.html#expiration-time-claim-exp
        raw_token = {
            # Expiration Time Claim
            # The “exp” (expiration time) claim identifies the expiration time 
            # on or after which the JWT MUST NOT be accepted for processing. 
            "exp": self.expire_after,
            "user_id": self.user_id,
        }
        encoded_token = jwt.encode(raw_token, JWT_SECRET, JWT_ALGORITHM)
        return encoded_token


class AuthToken(Token):

    def __init__(self, user_id: int) -> None:
        super().__init__(
            user_id=user_id,
            expire_after=now() + AUTH_TOKEN_EXPIRE_S,
        )
    
    @classmethod
    async def decode(cls, encoded_token) -> int:
        """
        Decode token from str and compare token->user_id mapping with cached token->user-id mapping.
        """
        user_id_token: int = await super().decode(encoded_token)
        user_id_cached: int = await cache.get(encoded_token)
        if not user_id_cached:
            raise UserAuthorizationException()
        if user_id_cached != user_id_token:
            logger.error(
                "Invalid user id from the encoded auth token. "
                f"user_id_cached={user_id_cached} and user_id_token={user_id_token}"
            )
            raise UserAuthorizationException()
        await cache.delete(encoded_token)
        return user_id_cached
    

    async def encode(self) -> str:
        encoded_token = await super().encode()
        await cache.set(encoded_token, self.user_id)
        return encoded_token


class AccessToken(Token):

    def __init__(self, user_id: int) -> None:
        super().__init__(
            user_id=user_id,
            expire_after=now() + ACCESS_TOKEN_EXPIRE_S,
        )



class TokenBearer():
    """
    Scheme that check the validity of auth_token that is exchanged
    to the authenticating user and return <User> if authorilized.
    """

    async def __call__(self, req: Request) -> Optional[User]:


        auth: str = req.cookies.get(COOKIE_TOKEN_KEY)
        logger.debug(f"AuthTokenBearer.__call__ is invoked with cookie {req.cookies} and auth={auth}")
        if not auth:
            logger.error(
                f"Authroization denied due to missing '{COOKIE_TOKEN_KEY}' "
                f"in the Request cookie: {req.headers}."
            )
            raise UserAuthorizationException()
        
        scheme, auth_token = get_authorization_scheme_param(auth)
        if scheme.lower() != "bearer":
            logger.error("Authroization denied due to invalid authorization_scheme: {scheme}. Expect: 'bearer'")
            raise UserAuthorizationException()

        user_id_verified = await self.__decode__(auth_token)
        user = User.get_by_id(user_id_verified)

        logger.debug(f"Get user: {user.name} with token: {auth_token}")
        return user

    async def __decode__(self, token_encoded: str) -> Token:
        return await Token.decode(token_encoded)


class AuthTokenBearer(TokenBearer):
    async def __decode__(self, token_encoded: str) -> Token:
        return await AuthToken.decode(token_encoded)


class AccessTokenBearer(TokenBearer):
    async def __decode__(self, token_encoded: str) -> Token:
        return await AccessToken.decode(token_encoded)
    


async def set_cookie_token(rsp: T, token: Token) -> T:
    token_encoded = await token.encode()
    rsp.set_cookie(
        key=COOKIE_TOKEN_KEY,
        value=f"Bearer {token_encoded}",
        httponly=True,
    )
    return rsp
        


def delete_cookie_token(rsp: T) -> T:
    rsp.delete_cookie(key=COOKIE_TOKEN_KEY)
    return rsp
