# ==============================================
# 文件名：step14_sqlalchemy_sync/database.py
# 基础功能：SQLAlchemy 数据库引擎和会话管理（同步模式，PostgreSQL）
# 核心学习知识点：
#   1. create_engine() — 创建数据库连接引擎，管理连接池
#   2. SessionLocal — 线程安全的数据库会话工厂
#   3. declarative_base() — ORM 模型基类
#   4. get_db() — FastAPI 依赖形式的会话生命周期管理
#   5. PostgreSQL 连接字符串 — postgresql+psycopg2://user:pass@host:port/dbname
#   6. 连接池参数 — pool_size / max_overflow / pool_pre_ping
# ==============================================
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ==============================================
# 数据库连接配置
# 【基础】连接字符串格式：postgresql+驱动://用户名:密码@主机:端口/数据库名
#   psycopg2 是 PostgreSQL 最成熟的 Python 同步驱动（C 扩展，性能好）
#   learnfast 是数据库名，运行前需要先在 PostgreSQL 中创建：
#     CREATE DATABASE learnfast;
# 【进阶】生产环境的数据库配置应从环境变量读取
#   绝不要把真实密码硬编码在代码中（本示例仅用于学习）
# ==============================================
DATABASE_URL = "postgresql+psycopg2://postgres:123456@localhost:5432/learnfast"

# ==============================================
# 创建数据库引擎
# 【基础】engine 是 SQLAlchemy 的核心，负责：
#   1. 管理数据库连接池（复用连接，避免每次请求都重新连接）
#   2. 将 Python 的 SQL 操作翻译为 PostgreSQL 能识别的 SQL
#   3. 执行事务管理（BEGIN/COMMIT/ROLLBACK）
# 【进阶】engine 参数详解：
#   pool_size=5 → 连接池保持 5 个常驻连接
#   max_overflow=10 → 高峰期额外创建最多 10 个连接（共 15 个峰值连接）
#   pool_pre_ping=True → 每次使用连接前先 SELECT 1 测试连通性
#     - 防止连接已被数据库服务端断开（超时断开）但客户端不知道
#     - 微小的性能代价换取极高的稳定性
#   echo=True → 打印所有 SQL 语句到控制台（调试神器，生产关闭）
# ==============================================
engine = create_engine(
    DATABASE_URL,
    pool_size=5,           # 连接池常驻连接数
    max_overflow=10,        # 溢出连接数（峰值 = pool_size + max_overflow）
    pool_pre_ping=True,     # 连接前测试有效性
    echo=True,              # 打印 SQL（学习用，生产环境必须关闭）
)

# ==============================================
# 创建会话工厂
# 【基础】SessionLocal 是"生产数据库会话的工厂"
#   每次调用 SessionLocal() 创建一个新的数据库会话
#   会话 = 一次数据库操作的单位（通常 = 一次 HTTP 请求）
# 【进阶】sessionmaker 参数：
#   autocommit=False → 手动提交事务（安全，推荐）
#     每次修改数据后须显式调用 db.commit()
#     如果忘了 commit，事务会在会话关闭时自动回滚
#   autoflush=False → 手动刷新更改到数据库
#     设为 False 避免查询前自动 flush 带来的意外性能开销
#   bind=engine → 告诉会话工厂用哪个 engine 管理连接
# ==============================================
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ==============================================
# 模型基类
# 【基础】所有 ORM 模型类都继承 Base
#   Base = declarative_base() 相当于 Python class 和数据库表之间的桥梁
#   ORM 模型 = Python class 继承 Base + 用 Column 定义字段
#   一张数据库表 = 一个继承 Base 的 Python 类
# 【进阶】declarative_base() 内部：
#   1. 创建一个元类（metaclass）来拦截类的定义
#   2. 扫描 Column 属性 → 生成 CREATE TABLE 语句
#   3. 维护类名 → __tablename__ 的映射表（metadata）
#   4. Base.metadata.create_all(engine) 一键创建所有表
# ==============================================
Base = declarative_base()


# ==============================================
# FastAPI 依赖：获取数据库会话
# 【基础】get_db() 是 FastAPI 的 yield 依赖函数
#   路径函数中写 db: Session = Depends(get_db)
#   请求开始时创建会话 → 路径函数使用 → 请求结束时关闭会话
# 【进阶】yield 依赖的事务安全性：
#   1. try/finally 确保无论什么情况（异常/正常），db.close() 都会被调用
#   2. 未提交的事务在 close() 时自动回滚（防止脏数据残留）
#   3. 连接归还到连接池（不是真正断开），下次请求可以复用
#   4. 每个请求独立 Session，不会互相干扰（线程安全）
# 常见错误：忘记 db.close() → 连接泄漏 → 耗尽连接池 → 服务不可用
#   yield 依赖的 finally 块彻底解决了"忘记关闭连接"的问题
# ==============================================
def get_db():
    """
    FastAPI 依赖：创建数据库会话，请求结束后自动关闭。
    用法：db: Session = Depends(get_db)
    """
    db = SessionLocal()  # setup：创建会话
    try:
        yield db           # 提供给路径函数
    finally:
        db.close()        # teardown：归还连接到池
