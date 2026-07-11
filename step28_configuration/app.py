# ==============================================
# 文件名：step28_configuration/app.py
# 基础功能：pydantic-settings 配置管理 — .env、环境变量、配置隔离
# 核心学习知识点：
#   1. pydantic-settings — 将配置从代码中分离到文件/环境变量
#   2. BaseSettings — 自动从 .env 和环境变量读取配置
#   3. SettingsConfigDict — env_file/env_prefix/case_sensitive 等配置项
#   4. @lru_cache — 缓存配置实例（避免重复读取 .env）
#   5. 环境隔离 — development / staging / production
#   6. 字段校验 — 配置也可以做 Pydantic 校验（如 min_length）
#   7. 敏感字段处理 — SecretStr 避免在日志中打印密码
#   8. 12-Factor App 配置原则 — 配置与代码分离
# 运行方式：uv run python -m step28_configuration.app
# ==============================================
import uvicorn
from functools import lru_cache

from fastapi import FastAPI, Depends
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ==============================================
# 配置类
# 【基础】继承 BaseSettings 后，自动从 .env 文件和环境变量读取配置
#         优先级：命令行 env > .env 文件 > 代码默认值
# 【进阶】BaseSettings 内部：
#   1. 扫描 SettingsConfigDict 中指定的 env_file
#   2. 解析 env_file 中的 KEY=VALUE 行
#   3. 按字段名匹配（不区分大小写，但区分下划线）
#   4. Pydantic 将字符串值转为字段声明的类型（int/list/bool 自动转换）
#   5. 所有字段都会经过 Field 中声明的校验规则
# ==============================================
class Settings(BaseSettings):
    """
    应用全局配置。
    model_config 中的 env_file 指定读取的文件。
    """
    model_config = SettingsConfigDict(
        env_file="step28_configuration/.env",  # 配置文件路径
        env_file_encoding="utf-8",
        case_sensitive=False,  # 大小写不敏感（推荐）
        extra="ignore",  # 忽略 .env 中未定义的键（不报错）
    )

    # --- 应用配置 ---
    app_name: str = Field(default="LearnFast", description="应用名称")
    app_version: str = Field(default="0.1.0")
    app_env: str = Field(default="development", description="环境：development/staging/production")

    # --- 数据库 ---
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/learnfast",
        description="数据库连接字符串（异步）",
    )
    database_pool_size: int = Field(default=5, ge=1, le=50)

    # --- JWT ---
    secret_key: SecretStr = Field(  # SecretStr 不会在日志/print 中打印明文
        default="dev-secret-key-change-in-production",
        min_length=32,
        description="JWT 签名密钥（至少 32 字符）",
    )
    access_token_expire_minutes: int = Field(default=30, ge=1)

    # --- CORS ---
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="允许的前端域名列表",
    )

    # --- 日志 ---
    log_level: str = Field(default="INFO", description="日志级别：DEBUG/INFO/WARNING/ERROR")

    @field_validator("app_env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        """校验环境名称必须是预定义值之一"""
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"app_env 必须是 {allowed} 之一，当前值: {v}")
        return v


# ==============================================
# 单例模式：缓存配置实例
# 【基础】@lru_cache 装饰器确保 settings 只创建一次（单例模式）
#         后续调用 get_settings() 直接返回缓存的实例
#         避免每次请求都重新读取 .env 文件
# 【进阶】@lru_cache 是 Python 标准库 functools 提供的装饰器
#   内部维护一个 dict：{函数参数 → 返回值}
#   相同参数调用 → 直接返回缓存值，不执行函数体
#   这里无参数 → 永远返回同一个实例
#   等价于模块级全局变量，但更优雅（可测试、延迟加载）
# ==============================================


@lru_cache
def get_settings() -> Settings:
    """获取配置单例（缓存）"""
    return Settings()


# ==============================================
# FastAPI 应用
# ==============================================
app = FastAPI(
    title="LearnFast API — 配置管理",
    description="FastAPI 学习 Step28：pydantic-settings + .env + 环境隔离",
    version="0.1.0",
)


# ==============================================
# 路由：展示配置内容
# ==============================================


@app.get("/config", tags=["config"])
def show_config(settings: Settings = Depends(get_settings)):
    """
    【基础功能】查看当前应用的配置（敏感字段自动隐藏）
    【学习知识点】
        1. Depends(get_settings) — 将配置实例注入路由
        2. SecretStr.get_secret_value() — 获取敏感字段的明文值
        3. 生产环境绝不应暴露此接口（仅学习演示用）
    """
    return {
        "app": {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
        },
        "database": {
            "url": settings.database_url,
            "pool_size": settings.database_pool_size,
        },
        "jwt": {
            "secret_key_length": len(settings.secret_key.get_secret_value()),
            "expire_minutes": settings.access_token_expire_minutes,
            # 注意：secret_key 本身不返回！SecretStr 的 __str__ 返回 "**********"
        },
        "cors": settings.cors_origins,
        "log_level": settings.log_level,
    }


@app.get("/info", tags=["info"])
def app_info(settings: Settings = Depends(get_settings)):
    """应用基本信息"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
    }


if __name__ == "__main__":
    uvicorn.run("step28_configuration.app:app", host="127.0.0.1", port=8000, reload=True)
