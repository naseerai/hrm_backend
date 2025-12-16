from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from src.login.login_routes import router as login_router
from src.common_routes.user_routes import router as user_router
app = FastAPI()
import logging
from starlette.middleware.trustedhost import TrustedHostMiddleware
from src.career_routes.careers_routes import router as careers_router
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])  # Temporary for testing

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(login_router)
app.include_router(user_router)
app.include_router(careers_router)

