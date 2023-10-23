DOMAIN = "https://127.0.0.1:8000"
LOGIN_REDIRECT_URL = "https://127.0.0.1:8000"

SSL_KEY_FILE = "<hide>" 
SSL_CERT_FILE = "<hide>" 

SQLITE_DB_FILE = "<hide>" 
# from cryptography.fernet import Fernet
# Fernet.generate_key()
FERNET_KEY = b'<hide>'
############# PROXY ############

RETURN_RESOURCE = 1 # Pure proxy, nothing but return drectly.
RETURN_RESOURCE_ID = 2 # write result into xdb and return id only
PROXY_MODE = RETURN_RESOURCE_ID

############# JWT ############
JWT_SECRET = "<hide>" 
JWT_ALGORITHM = "<hide>" 

AUTH_TOKEN_EXPIRE_S = 120
ACCESS_TOKEN_EXPIRE_S = 6 * 3600


############## Google ###############

# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
GOOGLE_CLIENT_SECRETS_FILE = "<hide>" 

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
# https://console.cloud.google.com/apis/credentials/consent?project=<project-name> to update scope
GOOGLE_SCOPES = [
    # Order matters
    "https://www.googleapis.com/auth/userinfo.email",
    "openid", # required by default.
]

############# OpenAI ###################
OPENAI_ORG_ID = "<hide>" 
OPENAI_API_KEY = "<hide>" 


############## Stripe ##############
# https://dashboard.stripe.com/test/apikeys
# Test keys
STRIPE_API_KEY = "<hide>" 
STRIPE_PRICE_ID = "<hide>" 
# TRIPE_PRICE_ID = "<hide>" 