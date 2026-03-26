FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY executor-python/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright
RUN pip install playwright && playwright install chromium

# 复制代码
COPY executor-python/ .

# 环境变量
ENV PYTHONPATH=/app
ENV NODE_ENV=production

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8002/health').raise_for_status()"

EXPOSE 8002

CMD ["uvicorn", "nova_executor.app:app", "--host", "0.0.0.0", "--port", "8002"]
