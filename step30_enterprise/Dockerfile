# ==============================================
# Dockerfile — 多阶段构建
# 【基础】第一阶段：编译依赖 → 第二阶段：精简运行镜像
#   最终镜像体积可缩减 80%+
# 【进阶】多阶段构建原理：
#   Stage 1 (builder): 安装完整 build 依赖，编译 wheel
#   Stage 2 (runtime): 只复制编译好的 wheel，不装编译器
#   结果：镜像从 ~1.2GB 降到 ~150MB
# ==============================================

# --- Stage 1: Build ---
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev

# --- Stage 2: Runtime ---
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . .
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "step30_enterprise.main:app", "--host", "0.0.0.0", "--port", "8000"]
