FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    ca-certificates \
    openssl \
    && rm -rf /var/lib/apt/lists/*

RUN pip config set global.index-url http://mirrors.cloud.tencent.com/pypi/simple && \
    pip config set global.trusted-host mirrors.cloud.tencent.com

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

# 启动命令，支持微信云托管的 PORT
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-80} run:app"]