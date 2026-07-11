# ==============================================
# 文件名：step17_alembic/env.py
# 基础功能：Alembic 迁移环境配置
# 核心学习知识点：
#   1. target_metadata — Alembic 根据 ORM 模型的 metadata 生成迁移
#   2. run_migrations_offline — 离线模式（生成 SQL 不执行）
#   3. run_migrations_online — 在线模式（连接数据库直接执行）
#   4. Base.metadata — SQLAlchemy 的"表注册表"
# ==============================================
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 加载 alembic.ini 中的配置
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 【基础】导入所有 ORM 模型，让 Alembic 知道有哪些表
# 【进阶】Alembic 通过 target_metadata 扫描模型定义
#   Base.metadata 是所有模型的注册表，Alembic 对比 metadata 和数据库实际结构生成迁移
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from step14_sqlalchemy_sync.models import User, Item
from step14_sqlalchemy_sync.database import Base

target_metadata = Base.metadata


def run_migrations_offline():
    """
    离线模式：生成 SQL 但不连接数据库执行。
    适合需要人工审核 SQL 或 DBA 手动执行的场景。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,  # 渲染参数为字面值（而非 %s 占位符）
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """在线模式：连接数据库直接执行迁移"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
