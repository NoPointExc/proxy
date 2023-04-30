from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from routers import user,  openai_v1

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
app.mount("/", StaticFiles(directory="static", html=True), name="index")



