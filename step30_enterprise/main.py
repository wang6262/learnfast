"""
step30_enterprise/main.py — 应用入口 + 工厂函数 + 路由汇总
"""
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.database import engine, Base
from .api.v1.router import router as v1_router
from .api.v2.router import router as v2_router
from .middleware.request_id import RequestIDMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


def create_app() -> FastAPI:
    """
    应用工厂函数。
    创建并配置 FastAPI 应用实例，注册所有中间件和路由。
    【进阶】工厂模式的优点：
      1. 一个代码库可以创建多个应用实例（web/api/admin）
      2. 测试时可以用不同配置创建应用
      3. 部署灵活（如灰度发布用不同配置启动不同实例）
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="企业级 FastAPI 分层架构示例",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID 中间件
    app.add_middleware(RequestIDMiddleware)

    # 注册路由
    app.include_router(v1_router, prefix="/api/v1", tags=["v1"])
    app.include_router(v2_router, prefix="/api/v2", tags=["v2"])

    # 健康检查
    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("step30_enterprise.main:app", host="127.0.0.1", port=8000, reload=True)
