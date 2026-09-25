from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from .config import API_DESCRIPTION, API_TITLE, API_VERSION, CORS_ORIGINS
    from .routes.forecast import router as forecast_router
except ImportError:
    from config import API_DESCRIPTION, API_TITLE, API_VERSION, CORS_ORIGINS
    from routes.forecast import router as forecast_router


app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(CORS_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "status": "running",
        "project": "Forecast Guard",
        "problem_statement": "26079",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


app.include_router(forecast_router)
