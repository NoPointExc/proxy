from typing import Any, Dict, Optional
import logging
import requests

from lib.exception import UserProfileNotFound, CanNotFoundEndPoint
from oauthlib.oauth2 import Client


logger = logging.getLogger("uvicorn.error")

DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

class GoogleOpenIdClient:

    def __init__(self, credentials: Any) -> None:
        # Following link for Credentials definition: 
        # https://github.com/googleapis/google-auth-library-python-oauthlib/blob/main/google_auth_oauthlib/helpers.py#L140
        logger.debug(
            f"get google client with client id={credentials.client_id}, token={credentials.token}"
            f"scopes={credentials.scopes}"
        )
        self.client = Client(
            client_id=credentials.client_id,
            refresh_token=credentials.refresh_token,
            access_token=credentials.token,
            scopes=credentials.scopes,
        )

        
    async def get_user_email(self) -> str:
        endpoint = await self._get_userinfo_endpoint()
        uri, headers, body = self.client.add_token(endpoint)
        userinfo_rsp = requests.get(uri, headers=headers, data=body)
        logger.debug(f"Got userinfo response:\n{userinfo_rsp}")
        userinfo_json = userinfo_rsp.json()
        logger.debug(f"usrinfo_json={userinfo_json}")

        # usrinfo_json={
        # 'sub': '123412312312312312',
        # 'picture': 'http:xxxx',
        # 'email': 'xxyyzzz@gmail.com',
        # 'email_verified': True}
        if userinfo_json.get("email_verified"):
            return userinfo_json["email"]
        logger.error(f"Failed to get user email from response json: {userinfo_json}")
        raise UserProfileNotFound("Failed to get user email")
    

    async def _get_userinfo_endpoint(self) -> str:
        doc: Optional[Dict[str, Any]] = None
        try:
            doc = requests.get(DISCOVERY_URL).json()
        except Exception as e:
            raise CanNotFoundEndPoint(
                f"Failed to get Google discovery doc from: {DISCOVERY_URL}"
            ) from e
        if "userinfo_endpoint" not in doc.keys():
            raise CanNotFoundEndPoint(
                f"Can not found 'userinfo_endpoint' from discovery doc:\n{doc}"
            )
        return doc["userinfo_endpoint"]