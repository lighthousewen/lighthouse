from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.api.v1.chat import router as chat_router
from app.api.v1.user import router as user_router
from app.api.v1.log import router as log_router
from app.api.internal import router as internal_router

app = FastAPI(
    title="Lighthouse API",
    version="0.1.0",
    description="灯塔 · 个人伙伴系统",
)


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(user_router)
app.include_router(log_router)
app.include_router(internal_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
