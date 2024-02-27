#!/usr/bin/env python3

import uvicorn
from lib.config import SSL_KEY_FILE, SSL_CERT_FILE


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        port=8000,
        host="0.0.0.0",
        log_level="debug",
        ssl_keyfile=SSL_KEY_FILE,
        ssl_certfile=SSL_CERT_FILE,
    )
