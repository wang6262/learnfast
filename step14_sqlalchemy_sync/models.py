# ==============================================
# 文件名：step14_sqlalchemy_sync/models.py
# 基础功能：SQLAlchemy ORM 模型定义 — User（用户）、Item（商品）
# 核心学习知识点：
#   1. Column() — 定义数据库表的列（字段）
#   2. 数据类型 — Integer, String, Boolean, Float, DateTime, Text, ForeignKey
#   3. primary_key=True — 主键（唯一标识一条记录，自动索引）
#   4. ForeignKey() — 外键关联（跨表引用）
#   5. relationship() — ORM 关系（通过 Python 对象导航到关联数据）
#   6. __tablename__ — 指定数据库表名
#   7. default= 参数 — server_default 在数据库层，default 在 Python 层
#   8. index=True — 为查询频繁的列创建索引
# ==============================================
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func  # 数据库函数（如 now()）

from database import Base  # 从同目录的 database.py 导入模型基类


# ==============================================
# 用户表模型
# 【基础】每个属性 = 数据库表的一个字段
#   id = Column(Integer, primary_key=True) → 整数自增主键
#   username = Column(String(50), unique=True) → 最长50字符，唯一索引
#   email = Column(String(100), nullable=False) → NOT NULL 约束
#   created_at = Column(DateTime, server_default=func.now()) → 默认当前时间
# 【进阶】Column 参数详解：
#   primary_key=True → 主键，自动 UNIQUE + NOT NULL + INDEX
#   unique=True → 唯一约束，创建唯一索引
#   nullable=False → NOT NULL 约束（数据库层）
#   index=True → 创建 B-Tree 索引，加速 WHERE/ORDER BY（但减慢 INSERT）
#   default= → Python 层的默认值（如 default=datetime.now 每次调用生成新值）
#   server_default= → 数据库层的默认值（如 server_default=func.now() → DEFAULT NOW()）
#     - server_default 更高效（不需要发送默认值到服务端）
#     - default 更灵活（支持 Python 侧动态生成默认值）
#   选择 default 还是 server_default：优先 server_default（数据库原生执行）
#   ForeignKey("other_table.id") → 外键约束，保证引用完整性
#     - ondelete="CASCADE" → 删除父记录时级联删除子记录
#     - ondelete="SET NULL" → 删除父记录时将子记录外键设为 NULL
# ==============================================
class User(Base):
    """用户表 ORM 模型"""
    __tablename__ = "users"  # 数据库中的表名

    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(100), nullable=False, unique=True, comment="邮箱")
    # phone = Column(String(20), nullable=False, unique=True, comment="电话号码")
    full_name = Column(String(100), comment="全名")
    hashed_password = Column(String(255), nullable=False, comment="bcrypt 密码哈希")
    is_active = Column(Boolean, default=True, server_default="true", comment="是否激活")
    role = Column(String(20), default="user", server_default="user", comment="角色")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 【基础】relationship 让 User 对象可以通过 .items 属性访问关联的商品
    # 【进阶】relationship() 参数：
    #   "Item" → 字符串引用（类名，避免循环导入）
    #   back_populates="owner" → 双向关系，Item.owner 对应 User.items
    #   lazy="select" → 懒加载（默认），访问 .items 时才查询数据库
    #   cascade="all, delete-orphan" → 级联操作（删除用户时删除其所有商品）
    # 备用写法：backref="owner" → 只在一边定义 relationship，另一边自动创建
    #   但 back_populates 更清晰（两边都显式声明），推荐使用
    items = relationship("Item", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        """调试用的字符串表示"""
        return f"<User(id={self.id}, username='{self.username}')>"


# ==============================================
# 商品表模型
# 【基础】ForeignKey("users.id") 建立外键关联
#   owner_id 指向 users 表的 id，表示这个商品属于哪个用户
#   每个商品必须有一个所有者（nullable=False）
# 【进阶】数据库关系设计：
#   一对多（One-to-Many）：User(1) → Items(N)
#     → 在"多"的一方（Item）放 ForeignKey 指向"一"的一方
#   多对多（Many-to-Many）：需要中间关联表（Step18 讲解）
#   一对一（One-to-One）：ForeignKey + unique=True
# ==============================================
class Item(Base):
    """商品表 ORM 模型"""
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True, comment="商品ID")
    name = Column(String(100), nullable=False, index=True, comment="商品名称")
    description = Column(Text, comment="商品描述（TEXT 类型支持长文本）")
    price = Column(Float, nullable=False, default=0.0, comment="价格")
    stock = Column(Integer, default=0, comment="库存数量")
    is_available = Column(Boolean, default=True, comment="是否在售")
    # 【基础】owner_id 外键指向 users 表的 id
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="所有者ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 【基础】反向关系：item.owner 获取商品的所有者（User 对象）
    owner = relationship("User", back_populates="items")

    def __repr__(self):
        return f"<Item(id={self.id}, name='{self.name}', price={self.price})>"
