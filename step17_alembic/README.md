# Step 17 — Alembic 数据库迁移

## 核心学习知识点
1. `alembic init` — 初始化迁移环境
2. `alembic revision --autogenerate` — 自动生成迁移脚本
3. `alembic upgrade head` — 升级到最新版本
4. `alembic downgrade -1` — 回退一个版本
5. `alembic history` — 查看迁移历史
6. `alembic current` — 查看当前版本

## 实战操作流程

### 1. 初始化迁移环境（一次性）
```bash
cd step17_alembic
alembic init alembic
```
将生成的 `alembic/` 目录和 `alembic.ini` 放在 step17_alembic 目录中。

### 2. 创建初始迁移
```bash
alembic revision --autogenerate -m "initial: create users and items tables"
```

### 3. 执行迁移（升级到最新）
```bash
alembic upgrade head
```

### 4. 修改模型后生成新迁移
```bash
# 修改 models.py（如给 users 表加 phone 列）
alembic revision --autogenerate -m "add phone column to users"
alembic upgrade head
```

### 5. 回退迁移
```bash
alembic downgrade -1          # 回退一个版本
alembic downgrade <revision>  # 回退到指定版本
```

### 6. 查看状态
```bash
alembic current   # 当前版本
alembic history   # 历史版本
```

## 注意事项
1. Alembic 是同步操作（使用 psycopg2），即使应用是异步的
2. --autogenerate 不总是完美的，复杂变更需手动编辑迁移脚本
3. 迁移脚本纳入版本控制（git），不要 .gitignore
4. 生产环境部署前先在测试环境验证迁移
